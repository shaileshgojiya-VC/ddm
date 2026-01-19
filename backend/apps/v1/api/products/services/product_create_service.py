"""
Service for creating products.
"""

import logging
from typing import List, Optional
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile

from apps.v1.api.products.models.model import Products
from apps.v1.api.products.models.methods import ProductRepository
from apps.v1.api.products.serializer import ProductSerializer
from apps.v1.api.suppliers.services.document_upload_service import DocumentUploadService

logger = logging.getLogger(__name__)


class ProductCreateService:
    """Service for creating product operations."""

    def __init__(self):
        self.document_upload_service = DocumentUploadService()

    async def create_product(
        self, 
        db: AsyncSession, 
        payload: dict,
        files: Optional[List[UploadFile]] = None,
        field_name: Optional[str] = None
    ) -> dict:
        """
        Create a single product from JSON payload.
        
        Args:
            db: Database session
            payload: Product data as JSON
            files: Optional list of files to upload as documents
            field_name: Optional field name for the documents (e.g., "certificate", "image")
        """
        logger.info("Creating new product")

        serializer = ProductSerializer()
        data = serializer.load(payload)

        xml_id = data.get("xml_id")
        if not xml_id:
            raise HTTPException(status_code=400, detail="ID/XML_ID is required")

        existing = await ProductRepository.fetch_product_by_xml_id(db, xml_id)
        if existing:
            raise HTTPException(status_code=409, detail="Product already exists")

        # Exclude 'id' field to ensure it remains autoincrement
        data.pop("id", None)

        try:
            await db.execute(insert(Products).values(data))
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating product with xml_id {xml_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

        new_product = await ProductRepository.fetch_product_by_xml_id(db, xml_id)
        if not new_product:
            logger.error(f"Product created but not found after commit: {xml_id}")
            raise HTTPException(
                status_code=500, detail="Product created but could not be retrieved"
            )

        logger.info(f"Product created successfully with xml_id: {xml_id}")
        
        # Handle document uploads if files are provided
        if files:
            try:
                uploaded_docs = await self.document_upload_service.upload_multiple_documents(
                    db=db,
                    files=files,
                    source_table="products",
                    mapping_id=new_product.id,
                    field_name=field_name,
                    source="api"
                )
                logger.info(f"Uploaded {len(uploaded_docs)} document(s) for product {new_product.id}")
            except Exception as e:
                # Log error but don't fail the create operation
                logger.warning(f"Failed to upload documents for product {new_product.id}: {e}")
        
        result = serializer.dump(new_product)

        # After successful creation, sync with webhook_data_service if bitrix_id exists
        # This ensures mappings and related data are properly handled
        if new_product.bitrix_id:
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
                    bitrix_id=str(new_product.bitrix_id),
                    mapping=mapping,
                )
                logger.info(f"Synced product {new_product.id} with webhook_data_service")
            except Exception as e:
                # Log error but don't fail the create operation
                logger.warning(
                    f"Failed to sync product {new_product.id} with webhook_data_service: {e}"
                )

        return result
