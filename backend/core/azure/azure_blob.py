"""
Azure Blob Storage Utilities

This module provides utilities for Azure Blob Storage operations.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from azure.storage.blob import ContentSettings, BlobType

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceNotFoundError, AzureError

from config.azure_config import (
    get_blob_service_client,
    get_container_client,
    get_blob_client,
)
from config.env_config import get_settings
from core.exceptions import ValidationException

# Get settings
settings = get_settings()


class AzureBlobService:
    """Service for Azure Blob Storage operations."""

    def __init__(self, container_name: Optional[str] = None):
        self.container_name = container_name or settings.AZURE_CONTAINER_NAME
        self.blob_service_client = get_blob_service_client()
        self.container_client = get_container_client(self.container_name)

    async def upload_file(
        self,
        file_content: bytes,
        blob_name: str,
        content_type: str = "application/octet-stream",
        metadata: dict = None,
        overwrite: bool = True,
    ) -> bool:
        """
        Upload file to Azure Blob Storage.

        Args:
            file_content: File content as bytes
            blob_name: Blob name
            content_type: MIME type of the file
            metadata: Optional metadata dictionary

        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            blob_client = get_blob_client(blob_name, self.container_name)

            blob_client.upload_blob(
                data=file_content,
                content_settings=ContentSettings(
                    content_type=content_type, cache_control="no-cache"
                ),
                metadata=metadata or {},
                overwrite=overwrite,
            )
            return True
        except AzureError as e:
            print(f"Azure Blob upload failed: {e}")
            return False

    async def download_file(self, blob_name: str) -> Optional[bytes]:
        """
        Download file from Azure Blob Storage.

        Args:
            blob_name: Blob name

        Returns:
            Optional[bytes]: File content if successful, None otherwise
        """
        try:
            blob_client = get_blob_client(blob_name, self.container_name)
            download_stream = blob_client.download_blob()
            return download_stream.readall()
        except ResourceNotFoundError:
            print(f"Blob not found: {blob_name}")
            return None
        except AzureError as e:
            print(f"Azure Blob download failed: {e}")
            return None

    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete file from Azure Blob Storage.

        Args:
            blob_name: Blob name

        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            blob_client = get_blob_client(blob_name, self.container_name)
            blob_client.delete_blob()
            return True
        except ResourceNotFoundError:
            print(f"Blob not found: {blob_name}")
            return False
        except AzureError as e:
            print(f"Azure Blob deletion failed: {e}")
            return False

    async def file_exists(self, blob_name: str) -> bool:
        """
        Check if file exists in Azure Blob Storage.

        Args:
            blob_name: Blob name

        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            blob_client = get_blob_client(blob_name, self.container_name)
            blob_client.get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False
        except AzureError:
            return False

    async def get_file_metadata(self, blob_name: str) -> Optional[Dict]:
        """
        Get file metadata from Azure Blob Storage.

        Args:
            blob_name: Blob name

        Returns:
            Optional[Dict]: File metadata if successful, None otherwise
        """
        try:
            blob_client = get_blob_client(blob_name, self.container_name)
            properties = blob_client.get_blob_properties()

            return {
                "size": properties.size,
                "last_modified": properties.last_modified,
                "content_type": properties.content_settings.content_type,
                "metadata": properties.metadata or {},
                "etag": properties.etag,
            }
        except ResourceNotFoundError:
            print(f"Blob not found: {blob_name}")
            return None
        except AzureError as e:
            print(f"Failed to get Azure Blob metadata: {e}")
            return None

    async def generate_presigned_url(
        self, blob_name: str, expiration: int = 3600, permission: str = "read"
    ) -> Optional[str]:
        """
        Generate presigned URL for Azure Blob.

        Args:
            blob_name: Blob name
            expiration: URL expiration time in seconds
            permission: Permission type ('read', 'write', 'delete')

        Returns:
            Optional[str]: Presigned URL if successful, None otherwise
        """
        try:
            blob_client = get_blob_client(blob_name, self.container_name)

            # Set permissions based on the permission parameter
            permissions = BlobSasPermissions(read=True)
            if permission == "write":
                permissions.write = True
            elif permission == "delete":
                permissions.delete = True

            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
                permission=permissions,
                expiry=datetime.now() + timedelta(seconds=expiration),
            )

            # Return full URL with SAS token
            return f"{blob_client.url}?{sas_token}"
        except AzureError as e:
            print(f"Failed to generate presigned URL: {e}")
            return None

    async def list_files(self, prefix: str = "", max_results: int = 1000) -> List[Dict]:
        """
        List files in Azure Blob Storage container.

        Args:
            prefix: Blob name prefix to filter by
            max_results: Maximum number of results to return

        Returns:
            List[Dict]: List of file information
        """
        try:
            blobs = self.container_client.list_blobs(
                name_starts_with=prefix, results_per_page=max_results
            )

            files = []
            for blob in blobs:
                files.append(
                    {
                        "name": blob.name,
                        "size": blob.size,
                        "last_modified": blob.last_modified,
                        "etag": blob.etag,
                        "content_type": (
                            blob.content_settings.content_type
                            if blob.content_settings
                            else None
                        ),
                    }
                )

            return files
        except AzureError as e:
            print(f"Failed to list Azure Blob files: {e}")
            return []

    async def copy_file(
        self,
        source_blob_name: str,
        destination_blob_name: str,
        source_container: Optional[str] = None,
    ) -> bool:
        """
        Copy file within Azure Blob Storage or from another container.

        Args:
            source_blob_name: Source blob name
            destination_blob_name: Destination blob name
            source_container: Source container (defaults to current container)

        Returns:
            bool: True if copy successful, False otherwise
        """
        try:
            source_container = source_container or self.container_name
            source_blob_client = get_blob_client(source_blob_name, source_container)
            destination_blob_client = get_blob_client(
                destination_blob_name, self.container_name
            )

            # Start copy operation
            copy_operation = destination_blob_client.start_copy_from_url(
                source_blob_client.url
            )

            # Wait for copy to complete (for small files this is usually immediate)
            destination_blob_client.get_blob_properties()

            return True
        except AzureError as e:
            print(f"Azure Blob copy failed: {e}")
            return False

    async def get_file_size(self, blob_name: str) -> Optional[int]:
        """
        Get file size from Azure Blob Storage.

        Args:
            blob_name: Blob name

        Returns:
            Optional[int]: File size in bytes if successful, None otherwise
        """
        metadata = await self.get_file_metadata(blob_name)
        return metadata.get("size") if metadata else None


# Global Azure Blob service instance
azure_blob_service = AzureBlobService()
