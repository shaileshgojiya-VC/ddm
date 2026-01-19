"""
Document Upload Service

This service handles uploading documents (images, PDFs, Word files) to Azure Blob Storage
and saving document metadata to the documents table for products, suppliers, and deals (requests).
"""

import logging
import mimetypes
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.azure.azure_blob import AzureBlobService
from apps.v1.api.suppliers.models.model import Documents
from config.env_config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class DocumentUploadService:
    """Service for uploading documents to Azure Blob Storage and saving to database."""

    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".rtf"}
    ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

    # Maximum file size: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

    def __init__(self):
        self.azure_blob_service = AzureBlobService()

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        if not filename:
            return ""
        return filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        extension = self._get_file_extension(filename)
        return f".{extension}" in self.ALLOWED_EXTENSIONS if extension else False

    def _detect_content_type(self, filename: str, file_content: bytes) -> str:
        """Detect MIME type from filename and content."""
        # First try mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        
        if content_type:
            return content_type
        
        # Fallback: detect from file signature
        if file_content:
            # Check for common file signatures
            if file_content.startswith(b"%PDF"):
                return "application/pdf"
            elif file_content.startswith(b"\x89PNG"):
                return "image/png"
            elif file_content.startswith(b"\xff\xd8\xff"):
                return "image/jpeg"
            elif file_content.startswith(b"GIF"):
                return "image/gif"
            elif file_content.startswith(b"PK\x03\x04"):
                # Could be .docx, .xlsx, etc.
                if filename.endswith(".docx"):
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif filename.endswith(".xlsx"):
                    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                return "application/zip"
        
        # Default fallback
        return "application/octet-stream"

    def _generate_blob_path(
        self, source_table: str, record_id: int, filename: str, field_name: Optional[str] = None
    ) -> str:
        """
        Generate Azure Blob Storage path.
        
        Format: documents/{source_table}/{record_id}/{field_name}/document_{uuid}{extension}
        """
        extension = self._get_file_extension(filename)
        file_id = str(uuid.uuid4())[:8]  # Short unique ID
        
        if field_name:
            # Clean field name (remove special characters)
            clean_field = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in field_name)
            return f"documents/{source_table}/{record_id}/{clean_field}/document_{file_id}.{extension}"
        else:
            return f"documents/{source_table}/{record_id}/document_{file_id}.{extension}"

    async def upload_document(
        self,
        db: AsyncSession,
        file: UploadFile,
        source_table: str,
        mapping_id: int,
        field_name: Optional[str] = None,
        source: str = "api",
    ) -> Dict[str, Any]:
        """
        Upload a single document to Azure Blob Storage and save metadata to database.
        
        Args:
            db: Database session
            file: UploadFile object from FastAPI
            source_table: Source table name (products, suppliers, requests)
            mapping_id: ID of the record in the source table
            field_name: Optional field name (e.g., "logo", "certificate")
            source: Source of the document (default: "api")
        
        Returns:
            Dict containing document information
        
        Raises:
            HTTPException: If file validation fails or upload fails
        """
        # Validate filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        if not self._is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        try:
            file_content = await file.read()
        except Exception as e:
            logger.error(f"Error reading file {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
        
        # Validate file size
        file_size = len(file_content)
        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Generate blob path
        blob_path = self._generate_blob_path(source_table, mapping_id, file.filename, field_name)
        
        # Detect content type
        content_type = self._detect_content_type(file.filename, file_content)
        
        # Upload to Azure Blob Storage
        logger.info(f"Uploading document to Azure Blob Storage: {blob_path}")
        upload_success = await self.azure_blob_service.upload_file(
            file_content=file_content,
            blob_name=blob_path,
            content_type=content_type,
            overwrite=True
        )
        
        if not upload_success:
            logger.error(f"Failed to upload document to Azure Blob Storage: {blob_path}")
            raise HTTPException(
                status_code=500,
                detail="Failed to upload document to Azure Blob Storage"
            )
        
        logger.info(f"Successfully uploaded document to Azure: {blob_path}")
        
        # Save document metadata to database
        try:
            now = datetime.now()
            
            # Build full Azure blob URL for url field
            azure_blob_storage_url = getattr(settings, "AZURE_BLOB_STORAGE_URL", None)
            if azure_blob_storage_url:
                azure_blob_storage_url = azure_blob_storage_url.rstrip("/")
                blob_url = f"{azure_blob_storage_url}/{blob_path}"
            else:
                blob_url = blob_path
            
            # For API uploads, there's no Bitrix URL data, so store empty JSON object in path
            import json
            path_json = json.dumps({})  # Empty dict since no Bitrix URL data for API uploads
            
            # Prepare document data
            document_data = {
                "path": path_json,  # Store empty JSON object (no Bitrix URL data for API uploads)
                "url": blob_url,  # Store full Azure blob storage URL
                "file_name": file.filename,
                "file_type": content_type,
                "file_size": file_size,
                "source": source,
                "mapping_id": mapping_id,
                "source_table": source_table,
                "created_at": now,
                "updated_at": now,
            }
            
            # Insert into documents table
            result = await db.execute(
                text("""
                    INSERT INTO documents 
                    (path, url, file_name, file_type, file_size, source, mapping_id, source_table, created_at, updated_at)
                    VALUES (:path, :url, :file_name, :file_type, :file_size, :source, :mapping_id, :source_table, :created_at, :updated_at)
                """),
                document_data
            )
            
            await db.commit()
            
            # Get the inserted document ID
            document_id_result = await db.execute(
                text("SELECT LAST_INSERT_ID() as id")
            )
            document_id = document_id_result.scalar()
            
            logger.info(f"Successfully saved document metadata to database (id: {document_id})")
            
            return {
                "id": document_id,
                "path": blob_path,
                "file_name": file.filename,
                "file_type": content_type,
                "file_size": file_size,
                "source": source,
                "mapping_id": mapping_id,
                "source_table": source_table,
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving document to database: {e}")
            # Try to delete from Azure if database insert fails
            try:
                await self.azure_blob_service.delete_file(blob_path)
            except Exception as delete_error:
                logger.error(f"Error deleting blob after database failure: {delete_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save document metadata: {str(e)}"
            )

    async def upload_multiple_documents(
        self,
        db: AsyncSession,
        files: List[UploadFile],
        source_table: str,
        mapping_id: int,
        field_name: Optional[str] = None,
        source: str = "api",
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple documents to Azure Blob Storage and save metadata to database.
        
        Args:
            db: Database session
            files: List of UploadFile objects
            source_table: Source table name (products, suppliers, requests)
            mapping_id: ID of the record in the source table
            field_name: Optional field name
            source: Source of the documents (default: "api")
        
        Returns:
            List of document information dictionaries
        """
        uploaded_documents = []
        errors = []
        
        for file in files:
            try:
                document = await self.upload_document(
                    db=db,
                    file=file,
                    source_table=source_table,
                    mapping_id=mapping_id,
                    field_name=field_name,
                    source=source,
                )
                uploaded_documents.append(document)
            except HTTPException as e:
                errors.append(f"{file.filename}: {e.detail}")
                logger.error(f"Error uploading {file.filename}: {e.detail}")
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
                logger.error(f"Unexpected error uploading {file.filename}: {e}")
        
        if errors and not uploaded_documents:
            # All uploads failed
            raise HTTPException(
                status_code=400,
                detail=f"All document uploads failed: {'; '.join(errors)}"
            )
        
        if errors:
            # Some uploads failed, but some succeeded
            logger.warning(f"Some document uploads failed: {'; '.join(errors)}")
        
        return uploaded_documents

