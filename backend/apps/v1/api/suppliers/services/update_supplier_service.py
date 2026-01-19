"""
Service to update suppliers.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.suppliers.serializer import SupplierSerializer
from apps.v1.api.suppliers.models.methods import (
    get_supplier_by_id as fetch_supplier_by_id,
    update_supplier_record,
)
from apps.v1.api.suppliers.services.document_upload_service import DocumentUploadService

logger = logging.getLogger(__name__)


class UpdateSupplierService:
    """Service for updating existing suppliers."""

    def __init__(self):
        self.document_upload_service = DocumentUploadService()

    async def update_supplier(
        self, 
        db: AsyncSession, 
        supplier_id: str, 
        payload: Dict[str, Any],
        files: Optional[List[UploadFile]] = None,
        field_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a single supplier by database id.
        
        Args:
            db: Database session
            supplier_id: Supplier database ID
            payload: Updated supplier data as JSON
            files: Optional list of files to upload as documents
            field_name: Optional field name for the documents
        """
        try:
            db_id = int(supplier_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Supplier ID must be a valid integer",
            )

        # Normalize and validate incoming payload
        mapped = SupplierSerializer().load(payload)

        # Filter out auto-generated fields (id is autoincrement, should not be updated from JSON)
        excluded_fields = {"id", "uuid", "created_at", "updated_at", "deleted_at"}
        clean_data = {k: v for k, v in mapped.items() if k not in excluded_fields}
        # Ensure id is not in clean_data (should not be updated)
        clean_data.pop("id", None)

        if not clean_data:
            raise HTTPException(
                status_code=400,
                detail="No updatable fields provided",
            )

        updated = await update_supplier_record(db=db, supplier_id=db_id, clean_data=clean_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Supplier not found")

        supplier = await fetch_supplier_by_id(db=db, supplier_id=db_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")

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
                # Log error but don't fail the update operation
                logger.warning(f"Failed to upload documents for supplier {supplier.id}: {e}")

        result = SupplierSerializer().dump(supplier)
        
        # After successful update, sync with webhook_data_service if bitrix_id exists
        # This ensures mappings and related data are properly handled
        if supplier.bitrix_id:
            try:
                import logging
                logger = logging.getLogger(__name__)
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
                    mapping=mapping
                )
                logger.info(f"Synced supplier {supplier.id} with webhook_data_service")
            except Exception as e:
                # Log error but don't fail the update operation
                logger.warning(f"Failed to sync supplier {supplier.id} with webhook_data_service: {e}")
        
        return result
