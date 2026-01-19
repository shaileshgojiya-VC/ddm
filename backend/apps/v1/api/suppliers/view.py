"""
Supplier API endpoints.
"""

import logging
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, Body, File, UploadFile, Form, Request, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import json

from apps.v1.api.suppliers.schema import SupplierFullSchema
from apps.v1.api.suppliers.services.create_supplier_service import CreateSupplierService
from apps.v1.api.suppliers.services.update_supplier_service import UpdateSupplierService
from apps.v1.api.suppliers.services.delete_supplier_service import DeleteSupplierService
from apps.v1.api.suppliers.services.list_supplier_service import ListSupplierService
from apps.v1.api.suppliers.services.get_supplier_detail_service import GetSupplierDetailService
from config.db_config import get_async_db
from core.utils import constant_variable
from core.utils.auth_dependencies import check_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix=constant_variable.API_V1_PREFIX, tags=["Supplier API"])


@router.post(
    "/supplier",
    response_model=SupplierFullSchema,
    summary="Create single supplier from JSON payload with optional document uploads",
)
async def create_supplier(
    request: Request,
    payload: Optional[str] = Form(None),
    payload_json: Optional[dict] = Body(None),
    files: Optional[List[UploadFile]] = File(None, description="Optional document files (images, PDFs, Word docs)"),
    field_name: Optional[str] = Form(None, description="Optional field name for documents (e.g., 'logo', 'certificate')"),
    current_user=Depends(check_permission("supplier_create")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new supplier from JSON payload with optional document uploads.
    Supports both JSON-only (application/json) and multipart/form-data requests.
    """
    logger.info("POST /supplier - create")
    
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
    
    service = CreateSupplierService()
    result = await service.create_supplier(
        db=db, 
        payload=payload_dict,
        files=files,
        field_name=field_name
    )
    logger.info("POST /supplier - created")
    return result


@router.get(
    "/suppliers",
    summary="List suppliers with filters, pagination, and sorting",
)
async def list_suppliers(
    search: Optional[str] = Query(
        None,
        description="Search suppliers by uuid, name, or email",
    ),
    country: Optional[str] = Query(
        None,
        description="Filter by country (United States, United Kingdom, India, etc.)",
    ),
    company_type: Optional[str] = Query(
        None,
        description="Filter by company type (manufacturer, distributor, retailer, other)",
    ),
    category_id: Optional[int] = Query(
        None,
        description="Filter by category id (1, 2, 3, etc.)",
    ),
    sub_category_id: Optional[int] = Query(
        None,
        description="Filter by sub_category id (1, 2, 3, etc.)",
    ),
    child_category_id: Optional[int] = Query(
        None,
        description="Filter by child_category id (1, 2, 3, etc.)",
    ),
    start_date: Optional[date] = Query(
        None,
        description="Filter by start date (YYYY-MM-DD format, e.g., 2025-01-01)",
    ),
    end_date: Optional[date] = Query(
        None,
        description="Filter by end date (YYYY-MM-DD format, e.g., 2025-01-31)",
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
    current_user=Depends(check_permission("supplier_read")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List suppliers with optional filters, sorting, and pagination.
    Returns paginated supplier list with metadata.
    """
    logger.info(
        f"GET /suppliers - search: {search}, country: {country}, company_type: {company_type}, "
        f"category_id: {category_id}, sub_category_id: {sub_category_id}, child_category_id: {child_category_id}, "
        f"start_date: {start_date}, end_date: {end_date}, "
        f"sort_by: {sort_by}, sort_order: {sort_order}, page: {page}, limit: {limit}"
    )
    service = ListSupplierService()
    result = await service.list_suppliers(
        db=db,
        search=search,
        country=country,
        company_type=company_type,
        category_id=category_id,
        sub_category_id=sub_category_id,
        child_category_id=child_category_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )
    logger.info("GET /suppliers - completed")
    return result


@router.get(
    "/supplier/{supplier_id}",
    summary="Get single supplier detail by database id",
)
async def get_supplier(
    supplier_id: str,
    current_user=Depends(check_permission("supplier_read")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get complete supplier details including products, price history, mail communication, and documents.
    Returns detailed supplier information with nested structures.
    """
    logger.info(f"GET /supplier/{supplier_id}")
    service = GetSupplierDetailService()
    result = await service.get_supplier_detail(db=db, supplier_id=supplier_id)
    logger.info(f"GET /supplier/{supplier_id} - completed")
    return result


@router.put(
    "/supplier/{supplier_id}",
    response_model=SupplierFullSchema,
    summary="Update single supplier by database id with optional document uploads",
)
async def update_supplier(
    supplier_id: str,
    request: Request,
    payload: Optional[str] = Form(None),
    payload_json: Optional[dict] = Body(None),
    files: Optional[List[UploadFile]] = File(None, description="Optional document files (images, PDFs, Word docs)"),
    field_name: Optional[str] = Form(None, description="Optional field name for documents"),
    current_user=Depends(check_permission("supplier_update")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update a single supplier by database id with optional document uploads.
    Supports both JSON-only (application/json) and multipart/form-data requests.
    """
    logger.info(f"PUT /supplier/{supplier_id}")
    
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
    
    service = UpdateSupplierService()
    result = await service.update_supplier(
        db=db, 
        supplier_id=supplier_id, 
        payload=payload_dict,
        files=files,
        field_name=field_name
    )
    logger.info(f"PUT /supplier/{supplier_id} - updated")
    return result


@router.delete(
    "/supplier/{supplier_id}",
    summary="Delete single supplier by database id (soft delete)",
)
async def delete_supplier(
    supplier_id: str,
    current_user=Depends(check_permission("supplier_delete")),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a single supplier by database id (soft delete)."""
    logger.info(f"DELETE /supplier/{supplier_id}")
    service = DeleteSupplierService()
    result = await service.delete_supplier(db=db, supplier_id=supplier_id)
    logger.info(f"DELETE /supplier/{supplier_id} - deleted")
    return result
