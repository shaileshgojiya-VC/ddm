"""
Service for updating products.
"""

import logging
from typing import List, Optional
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile

from apps.v1.api.products.models.model import Products
from apps.v1.api.products.models.methods import ProductRepository
from apps.v1.api.products.serializer import ProductSerializer
from apps.v1.api.suppliers.services.document_upload_service import DocumentUploadService

logger = logging.getLogger(__name__)


class ProductUpdateService:
    """Service for updating product operations."""

    def __init__(self):
        self.document_upload_service = DocumentUploadService()

    async def update_product(
        self, 
        db: AsyncSession, 
        product_id: str, 
        payload: dict,
        files: Optional[List[UploadFile]] = None,
        field_name: Optional[str] = None
    ) -> dict:
        """
        Update a single product by xml_id.
        
        Args:
            db: Database session
            product_id: Product xml_id
            payload: Updated product data as JSON
            files: Optional list of files to upload as documents
            field_name: Optional field name for the documents
        """
        logger.info(f"Updating product with xml_id: {product_id}")

        serializer = ProductSerializer()
        data = serializer.load(payload)

        # Force xml_id to match path param
        data["xml_id"] = product_id

        # Exclude 'id' field to prevent updating autoincrement ID
        data.pop("id", None)

        stmt = update(Products).where(Products.xml_id == product_id).values(**data)

        try:
            result = await db.execute(stmt)
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")

            await db.commit()
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating product with xml_id {product_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

        updated = await ProductRepository.fetch_product_by_xml_id(db, product_id)
        if not updated:
            logger.error(f"Product updated but not found after commit: {product_id}")
            raise HTTPException(
                status_code=500, detail="Product updated but could not be retrieved"
            )

        logger.info(f"Product updated successfully with xml_id: {product_id}")
        
        # Handle document uploads if files are provided
        if files:
            try:
                uploaded_docs = await self.document_upload_service.upload_multiple_documents(
                    db=db,
                    files=files,
                    source_table="products",
                    mapping_id=updated.id,
                    field_name=field_name,
                    source="api"
                )
                logger.info(f"Uploaded {len(uploaded_docs)} document(s) for product {updated.id}")
            except Exception as e:
                # Log error but don't fail the update operation
                logger.warning(f"Failed to upload documents for product {updated.id}: {e}")
        
        result = serializer.dump(updated)

        # After successful update, sync with webhook_data_service if bitrix_id exists
        # This ensures mappings and related data are properly handled
        if updated.bitrix_id:
            try:
                from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService

                webhook_service = WebhookDataService()
                # Extract mapping data from payload if present
                mapping = payload.get("mapping") or payload.get("mappings")
                if isinstance(mapping, dict):
                    mapping = [mapping]
                elif not isinstance(mapping, list):
                    mapping = None

                # Call webhook service to sync (this handles mappings, etc.)
                await webhook_service.update(
                    db=db,
                    table_name="products",
                    data=data,
                    bitrix_id=str(updated.bitrix_id),
                    mapping=mapping,
                )
                logger.info(f"Synced product {updated.id} with webhook_data_service")
            except Exception as e:
                # Log error but don't fail the update operation
                logger.warning(
                    f"Failed to sync product {updated.id} with webhook_data_service: {e}"
                )

        return result
