"""
Service to create new requests/deals.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select

from apps.v1.api.request.models.model import Requests
from apps.v1.api.request.serializer import RequestSerializer
from apps.v1.api.suppliers.services.document_upload_service import DocumentUploadService
from apps.v1.api.bitrix.models.methods import BitrixWebhookMethods

logger = logging.getLogger(__name__)


class CreateRequestService:
    """Service for creating new requests/deals."""

    def __init__(self):
        self.document_upload_service = DocumentUploadService()

    async def create_request(
        self, 
        db: AsyncSession, 
        payload: Dict[str, Any],
        files: Optional[List[UploadFile]] = None,
        field_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a single request/deal from incoming JSON payload.
        
        Args:
            db: Database session
            payload: Request/deal data as JSON
            files: Optional list of files to upload as documents
            field_name: Optional field name for the documents (e.g., "contract", "invoice")
        """
        logger.info("Creating new request/deal")
        
        # Normalize and validate the payload using serializer
        serializer = RequestSerializer()
        mapped = serializer.load(payload)

        # Filter out auto-generated fields
        excluded_fields = {"id", "uuid", "created_at", "updated_at", "deleted_at"}
        clean_data = {k: v for k, v in mapped.items() if k not in excluded_fields}
        clean_data.pop('id', None)

        # Map Bitrix user IDs to database user IDs
        clean_data = await self._map_bitrix_user_ids_to_db_ids(db, clean_data)

        try:
            # Check if a record with the same bitrix_id already exists
            bitrix_id = clean_data.get("bitrix_id")
            existing_request = None
            if bitrix_id:
                stmt = select(Requests).where(
                    Requests.bitrix_id == str(bitrix_id),
                    Requests.deleted_at.is_(None)
                ).limit(1)
                result = await db.execute(stmt)
                existing_request = result.scalar_one_or_none()
            
            if existing_request:
                # Record already exists, update it instead of creating a new one
                logger.info(f"Request with bitrix_id {bitrix_id} already exists (id: {existing_request.id}). Updating instead of creating.")
                from apps.v1.api.request.services.update_request_service import UpdateRequestService
                update_service = UpdateRequestService()
                return await update_service.update_request(
                    db=db,
                    request_id=str(existing_request.id),
                    payload=payload
                )
            
            # Create request instance (only if it doesn't exist)
            # Use try-except to handle race conditions where two requests try to insert simultaneously
            try:
                await db.execute(insert(Requests).values(clean_data))
                await db.commit()
            except Exception as insert_error:
                # Check if it's a duplicate key error (race condition)
                error_str = str(insert_error).lower()
                if "duplicate" in error_str or "1062" in error_str or "unique" in error_str:
                    # Another request with the same bitrix_id was inserted concurrently
                    # Fetch the existing record and update it instead
                    logger.warning(f"Duplicate key error during insert (race condition), fetching existing record: {insert_error}")
                    await db.rollback()
                    
                    if bitrix_id:
                        stmt = select(Requests).where(
                            Requests.bitrix_id == str(bitrix_id),
                            Requests.deleted_at.is_(None)
                        ).limit(1)
                        result = await db.execute(stmt)
                        existing_request = result.scalar_one_or_none()
                        
                        if existing_request:
                            # Update the existing record instead
                            logger.info(f"Found existing request (id: {existing_request.id}) after duplicate key error. Updating instead.")
                            from apps.v1.api.request.services.update_request_service import UpdateRequestService
                            update_service = UpdateRequestService()
                            return await update_service.update_request(
                                db=db,
                                request_id=str(existing_request.id),
                                payload=payload
                            )
                
                # If it's not a duplicate error, re-raise it
                raise
            
            # Fetch the created request
            bitrix_id = clean_data.get("bitrix_id")
            if bitrix_id:
                stmt = select(Requests).where(
                    Requests.bitrix_id == str(bitrix_id)
                ).order_by(Requests.id.desc()).limit(1)
            else:
                # Fallback: get by name or other unique field
                stmt = select(Requests).where(
                    Requests.name == clean_data.get("name")
                ).order_by(Requests.id.desc()).limit(1)
            
            result = await db.execute(stmt)
            request = result.scalar_one_or_none()
            
            if not request:
                raise HTTPException(status_code=500, detail="Request created but could not be retrieved")
            
            logger.info(f"Request created successfully with id: {request.id}")
            
            # Handle document uploads if files are provided
            if files:
                try:
                    uploaded_docs = await self.document_upload_service.upload_multiple_documents(
                        db=db,
                        files=files,
                        source_table="requests",
                        mapping_id=request.id,
                        field_name=field_name,
                        source="api"
                    )
                    logger.info(f"Uploaded {len(uploaded_docs)} document(s) for request {request.id}")
                except Exception as e:
                    # Log error but don't fail the create operation
                    logger.warning(f"Failed to upload documents for request {request.id}: {e}")
            
            result = serializer.dump(request)
            
            # Create RequestStageActivity records if deal_stage is present (regardless of bitrix_id)
            try:
                from apps.v1.api.bitrix.models.methods import BitrixWebhookMethods
                deal_stage = clean_data.get("deal_stage") or (request.deal_stage if hasattr(request, 'deal_stage') else None)
                phase = clean_data.get("phase") or (request.phase.value if hasattr(request, 'phase') and request.phase else None)
                current_stage_id = clean_data.get("current_stage_id") or (request.current_stage_id if hasattr(request, 'current_stage_id') else None)
                
                if deal_stage or current_stage_id:
                    await BitrixWebhookMethods.create_request_stage_activities(
                        db=db,
                        request_id=request.id,
                        deal_stage=deal_stage,
                        phase=phase,
                        current_stage_id=current_stage_id
                    )
                    logger.info(f"Created RequestStageActivity records for request {request.id}")
            except Exception as stage_error:
                # Log error but don't fail the create operation
                logger.warning(f"Failed to create RequestStageActivity for request {request.id}: {stage_error}")
            
            # After successful creation, sync with webhook_data_service if bitrix_id exists
            # This ensures mappings, deal_id generation, and activity logs are properly handled
            if request.bitrix_id:
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
                        bitrix_id=str(request.bitrix_id),
                        mapping=mapping
                    )
                    logger.info(f"Synced request {request.id} with webhook_data_service")
                except Exception as e:
                    # Log error but don't fail the create operation
                    logger.warning(f"Failed to sync request {request.id} with webhook_data_service: {e}")
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating request: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create request: {str(e)}")
    
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

