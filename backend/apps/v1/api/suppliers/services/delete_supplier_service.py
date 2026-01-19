"""
Service to delete suppliers (soft delete).
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService
from apps.v1.api.suppliers.models.methods import get_supplier_by_id
from apps.v1.api.suppliers.serializer import SupplierSerializer

logger = logging.getLogger(__name__)


class DeleteSupplierService:
    """Service for deleting suppliers (soft delete)."""

    async def delete_supplier(
        self, db: AsyncSession, supplier_id: str
    ) -> Dict[str, Any]:
        """Delete a single supplier by database id (soft delete)."""
        try:
            db_id = int(supplier_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Supplier ID must be a valid integer",
            )

        # Get supplier to retrieve bitrix_id
        supplier = await get_supplier_by_id(db=db, supplier_id=db_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")

        # Use webhook_data_service for soft delete (handles mappings and related records)
        webhook_service = WebhookDataService()
        bitrix_id = str(supplier.bitrix_id) if supplier.bitrix_id else None
        
        if not bitrix_id:
            # If no bitrix_id, use database ID as fallback
            bitrix_id = str(db_id)
            logger.warning(f"Supplier {db_id} has no bitrix_id, using database ID as fallback")

        result = await webhook_service.delete_record(
            db=db, table_name="suppliers", bitrix_id=bitrix_id
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete supplier: {result.get('message', 'Unknown error')}",
            )

        logger.info(f"Supplier {supplier_id} deleted successfully")
        return {
            "id": db_id,
            "bitrix_id": bitrix_id,
            "success": True,
            "message": "Supplier deleted successfully",
            "deleted_mappings": result.get("deleted_mappings", []),
        }

