"""
Bitrix24 webhook API endpoints.
"""

import json
import logging

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.bitrix.models.methods import BitrixWebhookMethods
from apps.v1.api.bitrix.schema import BitrixWebhookRequest, WebhookDataRequest
from apps.v1.api.bitrix.services.bitrix_webhook_service import BitrixWebhookService
from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService
from config.db_config import get_async_db
from core.utils import constant_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{constant_variable.API_V1_PREFIX}/bitrix", tags=["Bitrix24 Webhook API"])


@router.post("/webhook")
async def handle_bitrix_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle webhook notifications from Bitrix24.
    Supports JSON and form-urlencoded formats.
    """
    logger.info("=" * 80)
    logger.info("🔔 WEBHOOK REQUEST RECEIVED")
    logger.info(f"Method: {request.method}, URL: {request.url}")
    logger.info("=" * 80)
    
    try:
        content_type = request.headers.get("content-type", "")
        body_bytes = await request.body()

        if not body_bytes:
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message="Invalid webhook data: Empty request body",
            ).make

        # Parse request body
        raw_body = None
        if "application/json" in content_type:
            try:
                raw_body = json.loads(body_bytes.decode("utf-8"))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=f"Invalid webhook data: Failed to parse JSON - {str(e)}",
                ).make
        elif "application/x-www-form-urlencoded" in content_type:
            try:
                raw_body = BitrixWebhookMethods.parse_form_data(body_bytes.decode("utf-8"))
            except Exception as e:
                logger.error(f"Failed to parse form data: {e}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=f"Invalid webhook data: Failed to parse form data - {str(e)}",
                ).make
        else:
            # Fallback: try JSON first, then form
            try:
                raw_body = json.loads(body_bytes.decode("utf-8"))
            except json.JSONDecodeError:
                try:
                    raw_body = BitrixWebhookMethods.parse_form_data(body_bytes.decode("utf-8"))
                except Exception as e:
                    logger.error(f"Failed to parse body: {e}")
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_400_BAD_REQUEST,
                        data=constant_variable.STATUS_NULL,
                        message=f"Invalid webhook data: Failed to parse request body - {str(e)}",
                    ).make

        if not raw_body:
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message="Invalid webhook data: Could not parse request body",
            ).make

        # Ensure event field exists
        if "event" not in raw_body:
            raw_body["event"] = (
                request.query_params.get("event") or
                BitrixWebhookMethods.extract_event_from_path(str(request.url.path)) or
                "UNKNOWN"
            )
        
        # Ensure data field exists
        raw_body.setdefault("data", {})

        # Validate with Pydantic schema
        try:
            body = BitrixWebhookRequest(**raw_body)
        except Exception as ve:
            logger.error(f"Validation failed: {ve}")
            if "event" not in raw_body:
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=f"Invalid webhook data: Missing required 'event' field. {str(ve)}",
                ).make
            # Create minimal valid request
            body = BitrixWebhookRequest(
                event=raw_body.get("event", "UNKNOWN"),
                data=raw_body.get("data", {}),
                ts=raw_body.get("ts"),
                auth=raw_body.get("auth"),
            )

        logger.info(f"✅ Received Bitrix webhook: {body.event}")
        logger.info(f"📋 Raw webhook data: {json.dumps(raw_body, indent=2, default=str)}")

        # Process webhook
        try:
            service = BitrixWebhookService()
            result = await service.process_webhook(db=db, webhook_data=body)

            # Always return 200 OK to Bitrix24 (even on errors) to prevent retries
            if isinstance(result, dict) and result.get('status') == constant_variable.STATUS_FAIL:
                logger.warning("⚠️ Webhook processing failed but returning 200 OK to prevent retries")
                result['status_code'] = status.HTTP_200_OK
            
            logger.info("=" * 80)
            return result
        except Exception as service_exc:
            logger.error(f"❌ Error in webhook service: {service_exc}", exc_info=True)
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_200_OK,  # Return 200 to prevent Bitrix24 retries
                data=constant_variable.STATUS_NULL,
                message=f"Webhook received but processing failed: {str(service_exc)}",
            ).make

    except Exception as exc:
        logger.error(f"❌ Unexpected error: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_200_OK,  # Return 200 to prevent Bitrix24 retries
            data=constant_variable.STATUS_NULL,
            message=f"Webhook received but processing failed: {str(exc)}",
        ).make


@router.post("/data")
async def handle_webhook_data(
    payload: WebhookDataRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle webhook data operations (insert, update, delete) for all tables.
    
    Payload structure:
    {
        "eventtype": "insert" | "update" | "delete",
        "table": "product" | "supplier" | "customer" | "request" | etc.,
        "data": {
            // Table-related data (will be validated with serializer)
        },
        "bitrix_id": "123",  // Optional for insert, required for update/delete
        "mapping": [  // Optional, always in list format
            {
                "table": "bridge_table_name",
                "data": { ... }
            }
        ],
        "webhook": "bitrix" | "outlook"
    }
    """
    logger.info("=" * 80)
    logger.info("🔔 WEBHOOK DATA REQUEST RECEIVED")
    logger.info(f"Event Type: {payload.eventtype}, Table: {payload.table}, Webhook: {payload.webhook}")
    logger.info("=" * 80)

    try:
        service = WebhookDataService()
        result = await service.process_webhook_data(
            db=db,
            eventtype=payload.eventtype,
            table=payload.table,
            data=payload.data,
            bitrix_id=payload.bitrix_id,
            mapping=payload.mapping or [],
            webhook=payload.webhook,
        )

        logger.info(f"✅ Successfully processed {payload.eventtype} for {payload.table}")
        logger.info("=" * 80)

        return StandardResponse(
            status=constant_variable.STATUS_SUCCESS,
            status_code=status.HTTP_200_OK,
            data=result,
            message=f"Successfully processed {payload.eventtype} for {payload.table}",
        ).make

    except ValueError as ve:
        logger.error(f"❌ Validation error: {ve}")
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data={"webhook": payload.webhook},
            message=f"Validation error: {str(ve)}",
        ).make

    except Exception as exc:
        logger.error(f"❌ Error processing webhook data: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"webhook": payload.webhook},
            message=f"Error processing webhook data: {str(exc)}",
        ).make
