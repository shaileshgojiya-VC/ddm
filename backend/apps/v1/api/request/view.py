"""
Request API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException, Body, File, UploadFile, Form, Request
from typing import List, Optional
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import json


from apps.v1.api.request.services.list_all_stage import GetAllStageService
from apps.v1.api.request.services.list_request_service import ListRequestService
from apps.v1.api.request.services.get_request_detail_service import GetRequestDetailService
from apps.v1.api.request.services.create_request_service import CreateRequestService
from apps.v1.api.request.services.update_request_service import UpdateRequestService
from apps.v1.api.request.services.delete_request_service import DeleteRequestService
from config.db_config import get_async_db
from core.utils import constant_variable, message_variable
from core.utils.auth_dependencies import get_current_user, security
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix=constant_variable.API_V1_PREFIX, tags=["Request API"])


@router.get(
    "/request/list",
    summary="List requests with filters, pagination, and sorting",
)
async def list_requests(
    search: Optional[str] = Query(
        None,
        description="Search requests by uuid, customer_name, customer_email, bitrix_url, bitrix_id",
    ),
    priority: Optional[str] = Query(
        None,
        description="Filter by priority (urgent, high, medium, low)",
    ),
    phase: Optional[str] = Query(
        None,
        description="Filter by phase (lead, deal, registration)",
    ),
    request_status: Optional[str] = Query(
        None,
        description="Filter by status (active, inactive)",
    ),
    stage_id: Optional[int] = Query(
        None,
        description="Filter by stage id (1, 2, 3, etc.)",
    ),
    user_id: Optional[int] = Query(
        None,
        description="Filter by user id (1, 2, 3, etc.)",
    ),
    country: Optional[str] = Query(
        None,
        description="Filter by country (comma separated)",
    ),
    customer_id: Optional[int] = Query(
        None,
        description="Filter by customer id (1, 2, 3, etc.)",
    ),
    product_id: Optional[int] = Query(
        None,
        description="Filter by product id (1, 2, 3, etc.)",
    ),
    start_date: Optional[str] = Query(
        None,
        description="Filter by start date (YYYY-MM-DD)",
    ),
    end_date: Optional[str] = Query(
        None,
        description="Filter by end date (YYYY-MM-DD)",
    ),
    sort_by: Optional[str] = Query(
        None,
        description="Sort by field (created_at, updated_at)",
    ),
    sort_order: Optional[str] = Query(
        None,
        description="Sort order (asc, desc)",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List requests with optional filters, sorting, and pagination.
    Returns paginated request list with metadata.
    """
    logger.info(
        f"GET /request/list - search: {search}, priority: {priority}, phase: {phase}, "
        f"status: {request_status}, stage_id: {stage_id}, "
        f"user_id: {user_id}, country: {country}, customer_id: {customer_id}, "
        f"product_id: {product_id}, start_date: {start_date}, end_date: {end_date}, "
        f"sort_by: {sort_by}, sort_order: {sort_order}, page: {page}, limit: {limit}"
    )
    current_user = await get_current_user(authorize, db)

    service = ListRequestService()
    result = await service.list_requests(
        db=db,
        search=search,
        priority=priority,
        phase=phase,
        request_status=request_status,
        stage_id=stage_id,
        user_id=user_id,
        country=country,
        customer_id=customer_id,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
        current_user=current_user,
    )
    logger.info("GET /request/list - completed")
    return result


@router.get(
    "/request/stages",
    summary="Get all stages",
)
async def get_all_stages(
    phase: Optional[str] = Query(
        None,
        description="Filter by phase (lead, registration, deal)",
    ),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all stages with relationships.
    Returns stage list ordered by sequence for progress bar display.
    """
    logger.info(f"GET /request/stages - phase: {phase}")
    await get_current_user(authorize, db)

    service = GetAllStageService()
    result = await service.get_all_stages(db=db, phase=phase)
    logger.info("GET /request/stages - completed")
    return result


@router.get(
    "/request/{request_id}",
    summary="Get request detail by request_id",
)
async def get_request_detail(
    request_id: str,
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get request detail by request_id.
    """
    logger.info(f"GET /request/{request_id}")
    current_user = await get_current_user(authorize, db)
    service = GetRequestDetailService()
    try:
        result = await service.get_request_detail(
            db=db, request_id=request_id, current_user=current_user
        )
    except Exception as e:
        logger.error(f"GET /request/{request_id} - error: {e}")
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make
    finally:
        logger.info(f"GET /request/{request_id} - completed")
    return result


@router.post(
    "/request",
    summary="Create single request/deal from JSON payload with optional document uploads",
)
async def create_request(
    request: Request,
    payload: Optional[str] = Form(None),
    payload_json: Optional[dict] = Body(None),
    files: Optional[List[UploadFile]] = File(None, description="Optional document files (images, PDFs, Word docs)"),
    field_name: Optional[str] = Form(None, description="Optional field name for documents (e.g., 'contract', 'invoice')"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new request/deal from JSON payload with optional document uploads.
    Supports both JSON-only (application/json) and multipart/form-data requests.
    """
    logger.info("POST /request - create")
    current_user = await get_current_user(authorize, db)
    _ensure_access(current_user)
    
    # Determine payload source based on content type
    content_type = request.headers.get("content-type", "")
    payload_dict = None
    
    if "multipart/form-data" in content_type:
        # Multipart form data - use Form field
        if payload:
            try:
                payload_dict = json.loads(payload)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload in form data")
        else:
            raise HTTPException(status_code=400, detail="Payload is required")
    else:
        # JSON request - use Body
        if payload_json:
            payload_dict = payload_json
        else:
            raise HTTPException(status_code=400, detail="Payload is required")
    
    service = CreateRequestService()
    result = await service.create_request(
        db=db, 
        payload=payload_dict,
        files=files,
        field_name=field_name
    )
    logger.info("POST /request - created")
    return result


@router.put(
    "/request/{request_id}",
    summary="Update single request/deal by database id with optional document uploads",
)
async def update_request(
    request_id: str,
    request_obj: Request,
    payload: Optional[str] = Form(None),
    payload_json: Optional[dict] = Body(None),
    files: Optional[List[UploadFile]] = File(None, description="Optional document files (images, PDFs, Word docs)"),
    field_name: Optional[str] = Form(None, description="Optional field name for documents"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update a single request/deal by database id with optional document uploads.
    Supports both JSON-only (application/json) and multipart/form-data requests.
    """
    logger.info(f"PUT /request/{request_id}")
    current_user = await get_current_user(authorize, db)
    _ensure_access(current_user)
    
    # Determine payload source based on content type
    content_type = request_obj.headers.get("content-type", "")
    payload_dict = None
    
    if "multipart/form-data" in content_type:
        # Multipart form data - use Form field
        if payload:
            try:
                payload_dict = json.loads(payload)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload in form data")
        else:
            raise HTTPException(status_code=400, detail="Payload is required")
    else:
        # JSON request - use Body
        if payload_json:
            payload_dict = payload_json
        else:
            raise HTTPException(status_code=400, detail="Payload is required")
    
    service = UpdateRequestService()
    result = await service.update_request(
        db=db, 
        request_id=request_id, 
        payload=payload_dict,
        files=files,
        field_name=field_name
    )
    logger.info(f"PUT /request/{request_id} - updated")
    return result


@router.delete(
    "/request/{request_id}",
    summary="Delete single request/deal by database id (soft delete)",
)
async def delete_request(
    request_id: str,
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a single request/deal by database id (soft delete)."""
    logger.info(f"DELETE /request/{request_id}")
    current_user = await get_current_user(authorize, db)
    _ensure_access(current_user)
    service = DeleteRequestService()
    result = await service.delete_request(db=db, request_id=request_id)
    logger.info(f"DELETE /request/{request_id} - deleted")
    return result
