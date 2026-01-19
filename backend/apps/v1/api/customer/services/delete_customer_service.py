"""
Service to delete customers (soft delete).
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService
from apps.v1.api.customer.models.model import Customers

logger = logging.getLogger(__name__)


class DeleteCustomerService:
    """Service for deleting customers (soft delete)."""

    async def delete_customer(
        self, db: AsyncSession, customer_id: str
    ) -> Dict[str, Any]:
        """Delete a single customer by database id (soft delete)."""
        try:
            db_id = int(customer_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Customer ID must be a valid integer",
            )

        # Get customer to retrieve bitrix_id
        stmt = select(Customers).where(Customers.id == db_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Use webhook_data_service for soft delete (handles mappings and related records)
        webhook_service = WebhookDataService()
        bitrix_id = str(customer.bitrix_id) if customer.bitrix_id else None
        
        if not bitrix_id:
            # If no bitrix_id, use database ID as fallback
            bitrix_id = str(db_id)
            logger.warning(f"Customer {db_id} has no bitrix_id, using database ID as fallback")

        result = await webhook_service.delete_record(
            db=db, table_name="customers", bitrix_id=bitrix_id
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete customer: {result.get('message', 'Unknown error')}",
            )

        logger.info(f"Customer {customer_id} deleted successfully")
        return {
            "id": db_id,
            "bitrix_id": bitrix_id,
            "success": True,
            "message": "Customer deleted successfully",
            "deleted_mappings": result.get("deleted_mappings", []),
        }

