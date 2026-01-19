"""
Service to create new suppliers.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from apps.v1.api.suppliers.models.methods import create_supplier_record
from apps.v1.api.suppliers.serializer import SupplierSerializer
from apps.v1.api.suppliers.services.document_upload_service import DocumentUploadService

logger = logging.getLogger(__name__)


class CreateSupplierService:
    """Service for creating new suppliers."""

    def __init__(self):
        self.document_upload_service = DocumentUploadService()

    async def create_supplier(
        self, 
        db: AsyncSession, 
        payload: Dict[str, Any],
        files: Optional[List[UploadFile]] = None,
        field_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a single supplier from incoming JSON payload.
        
        Args:
            db: Database session
            payload: Supplier data as JSON
            files: Optional list of files to upload as documents
            field_name: Optional field name for the documents (e.g., "logo", "certificate")
        """
        # Normalize and validate the payload using the ingest schema
        mapped = SupplierSerializer().load(payload)

        # Filter out auto-generated fields (id is autoincrement, should not be set from JSON)
        excluded_fields = {"id", "uuid", "created_at", "updated_at", "deleted_at"}
        clean_data = {k: v for k, v in mapped.items() if k not in excluded_fields}
        # Ensure id is not in clean_data (should be autoincrement)
        clean_data.pop("id", None)

        # Create supplier instance
        supplier = await create_supplier_record(db=db, clean_data=clean_data)

        # Handle document uploads if files are provided
        if files:
            try:
                uploaded_docs = await self.document_upload_service.upload_multiple_documents(
                    db=db,
                    files=files,
                    source_table="suppliers",
                    mapping_id=supplier.id,
                    field_name=field_name,
                    source="api"
                )
                logger.info(f"Uploaded {len(uploaded_docs)} document(s) for supplier {supplier.id}")
            except Exception as e:
                # Log error but don't fail the create operation
                logger.warning(f"Failed to upload documents for supplier {supplier.id}: {e}")

        # Get the result first
        result = SupplierSerializer().dump(supplier)

        # After successful creation, sync with webhook_data_service if bitrix_id exists
        # This ensures mappings and related data are properly handled
        if supplier.bitrix_id:
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
                    table_name="suppliers",
                    data=clean_data,
                    bitrix_id=str(supplier.bitrix_id),
                    mapping=mapping,
                )
                logger.info(f"Synced supplier {supplier.id} with webhook_data_service")
            except Exception as e:
                # Log error but don't fail the create operation
                logger.warning(
                    f"Failed to sync supplier {supplier.id} with webhook_data_service: {e}"
                )

        # Return the created supplier
        return result
