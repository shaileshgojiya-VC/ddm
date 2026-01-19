"""
Service for deleting products (soft delete).
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService
from apps.v1.api.products.models.methods import ProductRepository
from apps.v1.api.products.serializer import ProductSerializer

logger = logging.getLogger(__name__)


class ProductDeleteService:
    """Service for deleting product operations (soft delete)."""

    async def delete_product(self, db: AsyncSession, product_id: str) -> dict:
        """Delete a single product by xml_id or database id (soft delete)."""
        logger.info(f"Deleting product with id: {product_id}")

        # Try to find product by ID or xml_id
        product = await ProductRepository.get_product_by_id(db, product_id)

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get bitrix_id for webhook service
        bitrix_id = str(product.bitrix_id) if product.bitrix_id else None
        
        if not bitrix_id:
            # If no bitrix_id, use database ID as fallback
            bitrix_id = str(product.id)
            logger.warning(f"Product {product_id} has no bitrix_id, using database ID as fallback")

        # Use webhook_data_service for soft delete (handles mappings and related records)
        webhook_service = WebhookDataService()
        result = await webhook_service.delete_record(
            db=db, table_name="products", bitrix_id=bitrix_id
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete product: {result.get('message', 'Unknown error')}",
            )

        logger.info(f"Product {product_id} deleted successfully")
        return {
            "id": product.id,
            "xml_id": product.xml_id,
            "bitrix_id": bitrix_id,
            "success": True,
            "message": "Product deleted successfully",
            "deleted_mappings": result.get("deleted_mappings", []),
        }

