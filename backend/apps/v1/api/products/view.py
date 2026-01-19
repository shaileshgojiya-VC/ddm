"""
Product API endpoints.
"""

import logging
from typing import Optional
from datetime import date

from fastapi import APIRouter, Body, Depends, Query, File, UploadFile, Form, Request, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import json

from apps.v1.api.products.schema import ProductFull
from apps.v1.api.products.services.list_category_service import ListCategoryService
from apps.v1.api.products.services.list_product_service import ListProductService
from apps.v1.api.products.services.product_create_service import ProductCreateService
from apps.v1.api.products.services.product_get_service import ProductGetService
from apps.v1.api.products.services.product_update_service import ProductUpdateService
from apps.v1.api.products.services.product_delete_service import ProductDeleteService
from config.db_config import get_async_db
from core.utils import constant_variable
from core.utils.auth_dependencies import check_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix=constant_variable.API_V1_PREFIX, tags=["Product API"])


@router.get(
    "/product/list",
    summary="List products with filters, pagination, and sorting",
)
async def list_products(
    search: Optional[str] = Query(
        None,
        description="Search products by id or name",
    ),
    category_id: Optional[str] = Query(
        None,
        description="Filter by category (dairy, beverages, snacks, personal care, home care, pet care, other)",
    ),
    sub_category_id: Optional[str] = Query(
        None,
        description="Filter by sub category",
    ),
    child_category_id: Optional[str] = Query(
        None,
        description="Filter by child category",
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
        "created_at",
        description="Sort by field (created_at, updated_at)",
    ),
    sort_order: Optional[str] = Query(
        "desc",
        description="Sort order (asc, desc)",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user=Depends(check_permission("product_read")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List products with optional filters, sorting, and pagination.

    Args:
        search: Search term for id or name
        category: Filter by category name
        parent_category: Filter by parent category name
        sub_category: Filter by sub-category name
        sort_by: Field to sort by (created_at, updated_at)
        sort_order: Sort order (asc, desc)
        page: Page number (default 1)
        limit: Items per page (default 10)
        current_user: Authenticated user with product_read permission
        db: Database session

    Returns:
        Paginated product list with metadata
    """
    logger.info(
        f"GET /product/list - search: {search}, category_id: {category_id}, "
        f"sub_category_id: {sub_category_id}, child_category_id: {child_category_id}, "
        f"start_date: {start_date}, end_date: {end_date}, "
        f"sort_by: {sort_by}, sort_order: {sort_order}, page: {page}, limit: {limit}"
    )
    service = ListProductService()
    result = await service.list_products(
        db=db,
        search=search,
        category_id=category_id,
        sub_category_id=sub_category_id,
        child_category_id=child_category_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by or "created_at",
        sort_order=sort_order or "desc",
        page=page,
        limit=limit,
    )
    logger.info("GET /product/list - completed")
    return result


@router.get(
    "/product/{product_id}",
    summary="Get product details by ID",
)
async def get_product_details(
    product_id: int,
    current_user=Depends(check_permission("product_read")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get complete product details by ID.

    Args:
        product_id: Product ID to retrieve
        current_user: Authenticated user with product_read permission
        db: Database session

    Returns:
        Complete product details including supplier, logistics, and documents
    """
    logger.info(f"GET /product/{product_id} - get details")
    service = ProductGetService()
    result = await service.get_product_details(db=db, product_id=product_id)
    logger.info(f"GET /product/{product_id} - completed")
    return result


@router.get(
    "/product/category/list",
    summary="List categories with hierarchy and product counts",
)
async def list_categories(
    search: Optional[str] = Query(
        None,
        description="Search categories by name",
    ),
    sort_by: Optional[str] = Query(
        "created_at",
        description="Sort by field (created_at, updated_at)",
    ),
    sort_order: Optional[str] = Query(
        "desc",
        description="Sort order (asc, desc)",
    ),
    current_user=Depends(check_permission("product_read")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List categories with child categories and product counts.

    Args:
        search: Search term for category name (case-insensitive)
        sort_by: Field to sort by (created_at, updated_at)
        sort_order: Sort order (asc, desc)
        current_user: Authenticated user with product_read permission
        db: Database session

    Returns:
        Category list with hierarchy and product counts
    """
    logger.info(
        f"GET /product/category/list - search: {search}, "
        f"sort_by: {sort_by}, sort_order: {sort_order}"
    )
    service = ListCategoryService()
    result = await service.list_categories(
        db=db,
        search=search,
        sort_by=sort_by or "created_at",
        sort_order=sort_order or "desc",
    )
    logger.info("GET /product/category/list - completed")
    return result


@router.post(
    "/product",
    response_model=ProductFull,
    summary="Create single product from JSON payload with optional document uploads",
)
async def create_product(
    request: Request,
    payload: Optional[str] = Form(None),
    payload_json: Optional[dict] = Body(None),
    files: Optional[List[UploadFile]] = File(None, description="Optional document files (images, PDFs, Word docs)"),
    field_name: Optional[str] = Form(None, description="Optional field name for documents (e.g., 'certificate', 'image')"),
    current_user=Depends(check_permission("product_create")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new product from JSON payload with optional document uploads.
    Supports both JSON-only (application/json) and multipart/form-data requests.

    Args:
        request: FastAPI request object
        payload: Product data as JSON string (for multipart/form-data requests)
        payload_json: Product data as JSON object (for application/json requests)
        files: Optional list of document files to upload (images, PDFs, Word docs)
        field_name: Optional field name for the documents
        current_user: Authenticated user with product_create permission
        db: Database session

    Returns:
        ProductFull: Created product data
    """
    logger.info("POST /product - create")
    
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
    
    service = ProductCreateService()
    result = await service.create_product(
        db=db, 
        payload=payload_dict,
        files=files,
        field_name=field_name
    )
    logger.info("POST /product - created")
    return result


@router.put(
    "/product/{product_id}",
    response_model=ProductFull,
    summary="Update single product by xml_id with optional document uploads",
)
async def update_product(
    product_id: str,
    request: Request,
    payload: Optional[str] = Form(None),
    payload_json: Optional[dict] = Body(None),
    files: Optional[List[UploadFile]] = File(None, description="Optional document files (images, PDFs, Word docs)"),
    field_name: Optional[str] = Form(None, description="Optional field name for documents"),
    current_user=Depends(check_permission("product_update")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update an existing product by ID or xml_id with optional document uploads.
    Supports both JSON-only (application/json) and multipart/form-data requests.

    Args:
        product_id: Product ID (integer as string) or xml_id
        request: FastAPI request object
        payload: Updated product data as JSON string (for multipart/form-data requests)
        payload_json: Updated product data as JSON object (for application/json requests)
        files: Optional list of document files to upload
        field_name: Optional field name for the documents
        current_user: Authenticated user with product_update permission
        db: Database session

    Returns:
        ProductFull: Updated product data
    """
    logger.info(f"PUT /product/{product_id} - update")
    
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
    
    service = ProductUpdateService()
    result = await service.update_product(
        db=db, 
        product_id=product_id, 
        payload=payload_dict,
        files=files,
        field_name=field_name
    )
    logger.info(f"PUT /product/{product_id} - updated")
    return result


@router.delete(
    "/product/{product_id}",
    summary="Delete single product by xml_id or database id (soft delete)",
)
async def delete_product(
    product_id: str,
    current_user=Depends(check_permission("product_delete")),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a single product by xml_id or database id (soft delete)."""
    logger.info(f"DELETE /product/{product_id}")
    service = ProductDeleteService()
    result = await service.delete_product(db=db, product_id=product_id)
    logger.info(f"DELETE /product/{product_id} - deleted")
    return result


@router.get(
    "/product/category/list",
    summary="List product categories with hierarchical structure",
)
async def list_categories(
    search: Optional[str] = Query(
        None,
        description="Search categories by name",
    ),
    sort_by: Optional[str] = Query(
        None,
        description="Sort by field (created_at, updated_at)",
    ),
    sort_order: Optional[str] = Query(
        None,
        description="Sort order (asc, desc)",
    ),
    current_user=Depends(check_permission("product_category_read")),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List product categories with optional search and sorting.
    Returns hierarchical category structure with child categories.
    """
    logger.info(
        f"GET /product/category/list - search: {search}, sort_by: {sort_by}, sort_order: {sort_order}"
    )
    service = ListCategoryService()
    result = await service.list_categories(
        db=db,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    logger.info("GET /product/category/list - completed")
    return result
