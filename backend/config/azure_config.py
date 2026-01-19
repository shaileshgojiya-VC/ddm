"""
Azure Blob Storage Configuration
"""
import os
from azure.storage.blob import BlobServiceClient
from config.env_config import get_settings

settings = get_settings()


def get_blob_service_client():
    """Get Azure Blob Service Client"""
    connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
    return BlobServiceClient.from_connection_string(connection_string)


def get_container_client(container_name: str):
    """Get Azure Container Client"""
    blob_service_client = get_blob_service_client()
    return blob_service_client.get_container_client(container_name)


def get_blob_client(blob_name: str, container_name: str):
    """Get Azure Blob Client"""
    blob_service_client = get_blob_service_client()
    return blob_service_client.get_blob_client(container=container_name, blob=blob_name)

