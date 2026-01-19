"""
Email collection API views/endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.email_collection.schema import (
    ConnectorCreateRequest,
    ConnectorListQueryParams,
    EmailListQueryParams,
    MailboxCreateRequest,
    MailboxListQueryParams,
    SpreadsheetSyncRequest,
    SubscriptionCreateRequest,
    WebhookNotificationRequest,
)
from apps.v1.api.email_collection.services.connector_create_service import (
    ConnectorCreateService,
)
from apps.v1.api.email_collection.services.connector_list_service import (
    ConnectorListService,
)
from apps.v1.api.email_collection.services.delta_sync_service import DeltaSyncService
from apps.v1.api.email_collection.services.email_list_service import EmailListService
from apps.v1.api.email_collection.services.email_processing_service import (
    EmailProcessingService,
)
from apps.v1.api.email_collection.services.mailbox_create_service import (
    MailboxCreateService,
)
from apps.v1.api.email_collection.services.mailbox_list_service import (
    MailboxListService,
)
from apps.v1.api.email_collection.services.spreadsheet_sync_service import (
    SpreadsheetSyncService,
)
from apps.v1.api.email_collection.services.subscription_create_service import (
    SubscriptionCreateService,
)
from apps.v1.api.email_collection.services.webhook_handler_service import (
    WebhookHandlerService,
)
from config.db_config import get_async_db
from core.utils import constant_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{constant_variable.API_V1_PREFIX}/email", tags=["Email Collection API"]
)


@router.post("/connectors")
async def create_connector(
    body: ConnectorCreateRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create email connector endpoint.

    Args:
        body: Connector creation request data
        db: Database session

    Returns:
        StandardResponse with created connector data
    """
    try:
        logger.info("Starting create connector endpoint")
        service = ConnectorCreateService()
        return await service.create_connector(db=db, request_data=body)
    except Exception as exc:
        logger.error(
            f"Unexpected error in create_connector endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.get("/connectors")
async def list_connectors(
    provider: str = Query(None, description="Filter by provider"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List email connectors endpoint.

    Args:
        provider: Filter by provider
        page: Page number
        limit: Number of items per page
        db: Database session

    Returns:
        StandardResponse with paginated connector list
    """
    try:
        logger.info("Starting list connectors endpoint")
        query_params = ConnectorListQueryParams(
            provider=provider, page=page, limit=limit
        )
        service = ConnectorListService()
        return await service.list_connectors(db=db, query_params=query_params)
    except Exception as exc:
        logger.error(
            f"Unexpected error in list_connectors endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.post("/mailboxes")
async def create_mailbox(
    body: MailboxCreateRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create email mailbox endpoint.

    Args:
        body: Mailbox creation request data
        db: Database session

    Returns:
        StandardResponse with created mailbox data
    """
    try:
        logger.info("Starting create mailbox endpoint")
        service = MailboxCreateService()
        return await service.create_mailbox(db=db, request_data=body)
    except Exception as exc:
        logger.error(
            f"Unexpected error in create_mailbox endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.get("/mailboxes")
async def list_mailboxes(
    email_auth_id: int = Query(None, description="Filter by email auth ID"),
    app_id: int = Query(None, description="Filter by app ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List email mailboxes endpoint.

    Args:
        email_auth_id: Filter by email auth ID
        app_id: Filter by app ID
        page: Page number
        limit: Number of items per page
        db: Database session

    Returns:
        StandardResponse with paginated mailbox list
    """
    try:
        logger.info("Starting list mailboxes endpoint")
        query_params = MailboxListQueryParams(
            email_auth_id=email_auth_id,
            app_id=app_id,
            page=page,
            limit=limit,
        )
        service = MailboxListService()
        return await service.list_mailboxes(db=db, query_params=query_params)
    except Exception as exc:
        logger.error(
            f"Unexpected error in list_mailboxes endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.post("/subscriptions")
async def create_subscription(
    body: SubscriptionCreateRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create webhook subscription endpoint.

    Args:
        body: Subscription creation request data
        db: Database session

    Returns:
        StandardResponse with created subscription data
    """
    try:
        logger.info("Starting create subscription endpoint")
        service = SubscriptionCreateService()
        return await service.create_subscription(db=db, request_data=body)
    except Exception as exc:
        logger.error(
            f"Unexpected error in create_subscription endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.post("/sync/spreadsheet")
async def sync_from_spreadsheet(
    file: UploadFile = File(..., description="Spreadsheet file (CSV or Excel)"),
    app_id: int = Form(..., description="Application ID"),
    email_column: str = Form(
        default="email", description="Column name containing email addresses"
    ),
    folder: str = Form(default="Inbox", description="Mailbox folder name"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Sync emails from spreadsheet endpoint.

    This endpoint:
    1. Reads email addresses from uploaded spreadsheet
    2. Uses existing connectors and subscriptions
    3. Syncs only emails that have conversations with spreadsheet emails
    4. Stores conversations in well-organized way

    Args:
        file: Spreadsheet file (CSV or Excel)
        app_id: Application ID
        email_column: Column name containing email addresses
        folder: Mailbox folder name
        db: Database session

    Returns:
        StandardResponse with sync results
    """
    try:
        logger.info("Starting spreadsheet sync endpoint")

        request_data = SpreadsheetSyncRequest(
            app_id=app_id,
            email_column=email_column,
            folder=folder,
        )

        service = SpreadsheetSyncService()
        return await service.sync_from_spreadsheet(
            db=db, file=file, request_data=request_data
        )
    except Exception as exc:
        logger.error(
            f"Unexpected error in sync_from_spreadsheet endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.post("/sync/{mailbox_id}")
async def trigger_delta_sync(
    mailbox_id: int,
    folder: str = Query("Inbox", description="Mailbox folder name"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Trigger delta sync for mailbox endpoint.

    Args:
        mailbox_id: Mailbox ID
        folder: Mailbox folder name
        db: Database session

    Returns:
        StandardResponse with sync results
    """
    try:
        logger.info(f"Starting delta sync endpoint for mailbox {mailbox_id}")
        service = DeltaSyncService()
        return await service.perform_delta_sync(
            db=db, mailbox_id=mailbox_id, folder=folder
        )
    except Exception as exc:
        logger.error(
            f"Unexpected error in trigger_delta_sync endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.get("/webhooks/outlook")
@router.post("/webhooks/outlook")
async def handle_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    body: Optional[WebhookNotificationRequest] = Body(None),
):
    """
    Handle webhook notification from Microsoft Graph endpoint.

    Microsoft Graph sends a validation request (GET) with validationToken query parameter
    during subscription creation. We must return the token as plain text with 200 OK.

    Args:
        request: FastAPI request object (to access query params)
        body: Webhook notification data (for POST requests)
        db: Database session

    Returns:
        Plain text validation token (for GET) or StandardResponse (for POST)
    """
    try:
        # Handle validation request (GET with validationToken)
        validation_token = request.query_params.get("validationToken")
        if validation_token:
            logger.info("Received webhook validation request from Microsoft Graph")
            # Return validation token as plain text (required by Microsoft Graph)
            return PlainTextResponse(content=validation_token, status_code=200)

        # Handle actual webhook notification (POST)
        if not body:
            logger.warning("Received POST request without body")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=400,
                data=constant_variable.STATUS_NULL,
                message="Missing request body",
            ).make

        logger.info("Starting webhook handler endpoint")
        service = WebhookHandlerService()
        return await service.handle_webhook(db=db, notification_data=body.dict())
    except Exception as exc:
        logger.error(
            f"Unexpected error in handle_webhook endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.get("/emails")
async def list_emails(
    mailbox_id: int = Query(None, description="Filter by mailbox ID"),
    conversation_id: int = Query(None, description="Filter by conversation ID"),
    search: str = Query(None, description="Search in subject or sender"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List emails endpoint.

    Args:
        mailbox_id: Filter by mailbox ID
        conversation_id: Filter by conversation ID
        search: Search in subject or sender
        page: Page number
        limit: Number of items per page
        db: Database session

    Returns:
        StandardResponse with paginated email list
    """
    try:
        logger.info("Starting list emails endpoint")
        query_params = EmailListQueryParams(
            mailbox_id=mailbox_id,
            conversation_id=conversation_id,
            search=search,
            page=page,
            limit=limit,
        )
        service = EmailListService()
        return await service.list_emails(db=db, query_params=query_params)
    except Exception as exc:
        logger.error(f"Unexpected error in list_emails endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make


@router.get("/emails/email_address")
async def get_emails_by_address(
    email: str = Query(..., description="Email address to search for"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all emails for a given email address endpoint.

    Returns all emails where the given email address is either sender or receiver,
    formatted according to EmailProcessingSerializer.

    Args:
        email: Email address to search for
        db: Database session

    Returns:
        StandardResponse with list of email processing data
    """
    try:
        logger.info(f"Starting get emails by address endpoint for: {email}")
        service = EmailProcessingService()
        return await service.get_emails_by_address(db=db, email_address=email)
    except Exception as exc:
        logger.error(
            f"Unexpected error in get_emails_by_address endpoint: {exc}", exc_info=True
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=500,
            data=constant_variable.STATUS_NULL,
            message="Something went wrong",
        ).make
