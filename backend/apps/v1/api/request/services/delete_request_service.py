"""
Service to delete requests/deals (soft delete).
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService
from apps.v1.api.request.models.model import Requests

logger = logging.getLogger(__name__)


class DeleteRequestService:
    """Service for deleting requests/deals (soft delete)."""

    async def delete_request(
        self, db: AsyncSession, request_id: str
    ) -> Dict[str, Any]:
        """Delete a single request/deal by database id (soft delete)."""
        try:
            db_id = int(request_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Request ID must be a valid integer",
            )

        # Get request to retrieve bitrix_id
        stmt = select(Requests).where(Requests.id == db_id)
        result = await db.execute(stmt)
        request = result.scalar_one_or_none()

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        # Use webhook_data_service for soft delete (handles mappings and related records)
        webhook_service = WebhookDataService()
        bitrix_id = str(request.bitrix_id) if request.bitrix_id else None
        
        if not bitrix_id:
            # If no bitrix_id, use database ID as fallback
            bitrix_id = str(db_id)
            logger.warning(f"Request {db_id} has no bitrix_id, using database ID as fallback")

        result = await webhook_service.delete_record(
            db=db, table_name="requests", bitrix_id=bitrix_id
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete request: {result.get('message', 'Unknown error')}",
            )

        logger.info(f"Request {request_id} deleted successfully")
        return {
            "id": db_id,
            "bitrix_id": bitrix_id,
            "success": True,
            "message": "Request deleted successfully",
            "deleted_mappings": result.get("deleted_mappings", []),
        }

