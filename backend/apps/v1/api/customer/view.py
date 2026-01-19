"""
Customer API endpoints.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.customer.services.create_customer_service import CreateCustomerService
from apps.v1.api.customer.services.update_customer_service import UpdateCustomerService
from apps.v1.api.customer.services.delete_customer_service import DeleteCustomerService
from config.db_config import get_async_db
from core.utils import constant_variable
from core.utils.auth_dependencies import check_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix=constant_variable.API_V1_PREFIX, tags=["Customer API"])


@router.post(
    "/customer",
    summary="Create single customer from JSON payload",
)
async def create_customer(
    payload: dict = Body(...),
    current_user=Depends(check_permission("customer_create")),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new customer from JSON payload."""
    logger.info("POST /customer - create")
    service = CreateCustomerService()
    result = await service.create_customer(db=db, payload=payload)
    logger.info("POST /customer - created")
    return result


@router.put(
    "/customer/{customer_id}",
    summary="Update single customer by database id",
)
async def update_customer(
    customer_id: str,
    payload: dict = Body(...),
    current_user=Depends(check_permission("customer_update")),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a single customer by database id."""
    logger.info(f"PUT /customer/{customer_id}")
    service = UpdateCustomerService()
    result = await service.update_customer(db=db, customer_id=customer_id, payload=payload)
    logger.info(f"PUT /customer/{customer_id} - updated")
    return result


@router.delete(
    "/customer/{customer_id}",
    summary="Delete single customer by database id (soft delete)",
)
async def delete_customer(
    customer_id: str,
    current_user=Depends(check_permission("customer_delete")),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a single customer by database id (soft delete)."""
    logger.info(f"DELETE /customer/{customer_id}")
    service = DeleteCustomerService()
    result = await service.delete_customer(db=db, customer_id=customer_id)
    logger.info(f"DELETE /customer/{customer_id} - deleted")
    return result

