"""
Service to update requests/deals.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.request.models.model import Requests
from apps.v1.api.request.serializer import RequestSerializer
from apps.v1.api.suppliers.services.document_upload_service import DocumentUploadService
from apps.v1.api.bitrix.models.methods import BitrixWebhookMethods

logger = logging.getLogger(__name__)


class UpdateRequestService:
    """Service for updating existing requests/deals."""

    def __init__(self):
        self.document_upload_service = DocumentUploadService()

    async def update_request(
        self, 
        db: AsyncSession, 
        request_id: str, 
        payload: Dict[str, Any],
        files: Optional[List[UploadFile]] = None,
        field_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a single request/deal by database id.
        
        Args:
            db: Database session
            request_id: Request database ID
            payload: Updated request/deal data as JSON
            files: Optional list of files to upload as documents
            field_name: Optional field name for the documents
        """
        try:
            db_id = int(request_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Request ID must be a valid integer",
            )

        # Normalize and validate incoming payload
        serializer = RequestSerializer()
        mapped = serializer.load(payload)

        # Filter out auto-generated fields
        excluded_fields = {"id", "uuid", "created_at", "updated_at", "deleted_at"}
        clean_data = {k: v for k, v in mapped.items() if k not in excluded_fields}
        clean_data.pop('id', None)

        # Map Bitrix user IDs to database user IDs
        clean_data = await self._map_bitrix_user_ids_to_db_ids(db, clean_data)

        if not clean_data:
            raise HTTPException(
                status_code=400,
                detail="No updatable fields provided",
            )

        # Check if request exists
        stmt = select(Requests).where(Requests.id == db_id)
        result = await db.execute(stmt)
        request = result.scalar_one_or_none()

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        try:
            # Update request
            update_stmt = (
                update(Requests)
                .where(Requests.id == db_id)
                .values(**clean_data)
            )
            await db.execute(update_stmt)
            await db.commit()

            # Fetch updated request
            result = await db.execute(stmt)
            updated_request = result.scalar_one_or_none()

            if not updated_request:
                raise HTTPException(status_code=500, detail="Request updated but could not be retrieved")

            logger.info(f"Request {request_id} updated successfully")
            
            # Handle document uploads if files are provided
            if files:
                try:
                    uploaded_docs = await self.document_upload_service.upload_multiple_documents(
                        db=db,
                        files=files,
                        source_table="requests",
                        mapping_id=updated_request.id,
                        field_name=field_name,
                        source="api"
                    )
                    logger.info(f"Uploaded {len(uploaded_docs)} document(s) for request {updated_request.id}")
                except Exception as e:
                    # Log error but don't fail the update operation
                    logger.warning(f"Failed to upload documents for request {updated_request.id}: {e}")
            
            result = serializer.dump(updated_request)
            
            # After successful update, sync with webhook_data_service if bitrix_id exists
            # This ensures mappings, deal_id regeneration, and activity logs are properly handled
            if updated_request.bitrix_id:
                try:
                    from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService
                    webhook_service = WebhookDataService()
                    # Extract mapping data from payload if present
                    mapping = payload.get("mapping") or payload.get("mappings")
                    if isinstance(mapping, dict):
                        mapping = [mapping]
                    elif not isinstance(mapping, list):
                        mapping = None
                    
                    # Call webhook service to sync (this handles mappings, deal_id, activity logs, etc.)
                    await webhook_service.update(
                        db=db,
                        table_name="requests",
                        data=clean_data,
                        bitrix_id=str(updated_request.bitrix_id),
                        mapping=mapping
                    )
                    logger.info(f"Synced request {updated_request.id} with webhook_data_service")
                except Exception as e:
                    # Log error but don't fail the update operation
                    logger.warning(f"Failed to sync request {updated_request.id} with webhook_data_service: {e}")
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating request {request_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update request: {str(e)}")
    
    async def _map_bitrix_user_ids_to_db_ids(
        self, db: AsyncSession, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map Bitrix user IDs to database user IDs for request fields.
        - Maps responsible_person (Bitrix ID) to assigned_by (user ID)
        - Maps observer_bitrixids (array of Bitrix IDs) to observer_ids (array of user IDs)
        - Also handles assigned_by if it's already set but contains a Bitrix ID
        """
        import json
        from sqlalchemy import select
        from apps.v1.api.auth.models.model import Users
        
        # Helper function to resolve user ID (try Bitrix ID first, then check if it's a database ID)
        async def resolve_user_id(value: int) -> Optional[int]:
            """Resolve a user ID - try as Bitrix ID first, then check if it's a valid database ID."""
            if not isinstance(value, int):
                return None
            
            # First, try to find by Bitrix ID
            db_user_id = await BitrixWebhookMethods.get_user_id_by_bitrix_id(db, value)
            if db_user_id:
                return db_user_id
            
            # If not found by Bitrix ID, check if it's a valid database user ID
            user_exists = await db.execute(
                select(Users.id).where(Users.id == value).limit(1)
            )
            if user_exists.scalar_one_or_none():
                return value
            
            # Not found as Bitrix ID or database ID
            return None
        
        # First, check if assigned_by is already set but might be a Bitrix ID
        if "assigned_by" in data and data["assigned_by"]:
            assigned_by_value = data["assigned_by"]
            # Convert to int if it's a string
            if isinstance(assigned_by_value, str):
                try:
                    assigned_by_value = int(assigned_by_value)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert assigned_by '{assigned_by_value}' to integer. Removing to avoid FK constraint error.")
                    data.pop("assigned_by", None)
                    assigned_by_value = None
            
            if assigned_by_value and isinstance(assigned_by_value, int):
                # Find user in users table where bitrix_id = assigned_by_value, get their database id
                resolved_id = await resolve_user_id(assigned_by_value)
                if resolved_id:
                    if resolved_id != assigned_by_value:
                        # Store the database user id in assigned_by column
                        data["assigned_by"] = resolved_id
                        logger.info(f"Mapped assigned_by Bitrix ID {assigned_by_value} to user ID {resolved_id} (found user with bitrix_id={assigned_by_value} has database id={resolved_id})")
                else:
                    # User not found in users table, remove assigned_by to avoid FK constraint error
                    logger.warning(f"Could not find user in users table with bitrix_id={assigned_by_value} for assigned_by. Removing to avoid FK constraint error.")
                    data.pop("assigned_by", None)
        
        # Map responsible_person to assigned_by (only if assigned_by is not already set)
        if "responsible_person" in data and data["responsible_person"] and "assigned_by" not in data:
            bitrix_id = data["responsible_person"]
            try:
                # Convert to int if it's a string (e.g., "218" -> 218)
                if isinstance(bitrix_id, str):
                    try:
                        bitrix_id = int(bitrix_id)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert responsible_person '{bitrix_id}' to integer. Skipping assigned_by mapping.")
                        bitrix_id = None
                
                if bitrix_id and isinstance(bitrix_id, int):
                    # Find user in users table where bitrix_id = 218, get their database id (e.g., 5)
                    resolved_id = await resolve_user_id(bitrix_id)
                    if resolved_id:
                        # Store the database user id (e.g., 5) in assigned_by column
                        data["assigned_by"] = resolved_id
                        logger.info(f"Mapped responsible_person Bitrix ID {bitrix_id} to assigned_by user ID {resolved_id} (found user with bitrix_id={bitrix_id} has database id={resolved_id})")
                    else:
                        # User not found in users table with this bitrix_id, don't set assigned_by to avoid FK constraint error
                        logger.warning(f"Could not find user in users table with bitrix_id={bitrix_id} for assigned_by mapping. Skipping assigned_by.")
            except Exception as e:
                logger.error(f"Error mapping responsible_person to assigned_by: {e}")
        
        # Map observer_bitrixids to observer_ids
        if "observer_bitrixids" in data and data["observer_bitrixids"]:
            observer_bitrixids = data["observer_bitrixids"]
            observer_ids = []
            
            # Handle different input formats
            if isinstance(observer_bitrixids, str):
                # Try to parse as JSON
                try:
                    observer_bitrixids = json.loads(observer_bitrixids)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse observer_bitrixids as JSON: {observer_bitrixids}")
                    observer_bitrixids = []
            
            if isinstance(observer_bitrixids, list):
                for bitrix_id in observer_bitrixids:
                    if not bitrix_id:
                        continue
                    try:
                        if isinstance(bitrix_id, int):
                            # Try to resolve user ID (Bitrix ID or database ID)
                            resolved_id = await resolve_user_id(bitrix_id)
                            if resolved_id:
                                observer_ids.append(resolved_id)
                                if resolved_id != bitrix_id:
                                    logger.debug(f"Mapped observer Bitrix ID {bitrix_id} to user ID {resolved_id}")
                            else:
                                logger.warning(f"Could not find user with ID/Bitrix ID {bitrix_id} for observer_ids mapping")
                    except Exception as e:
                        logger.error(f"Error mapping observer Bitrix ID {bitrix_id} to user ID: {e}")
            
            data["observer_ids"] = observer_ids if observer_ids else None
            logger.info(f"Mapped {len(observer_ids)} observer Bitrix IDs to user IDs")
        
        return data

