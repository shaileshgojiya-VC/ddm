"""
Service to handle insert, update, and delete operations for all tables via webhook.
"""

import json
import logging
import time
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type, Tuple
from sqlalchemy import text as sql_text_lock
from sqlalchemy import select, text
from sqlalchemy import text as sql_text_check
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text
                    
from apps.v1.api.products.models.model import Products, Categories
from apps.v1.api.products.serializer import ProductSerializer, CategorySerializer
from apps.v1.api.suppliers.models.model import Suppliers
from apps.v1.api.suppliers.serializer import SupplierSerializer
from apps.v1.api.customer.models.model import Customers
from apps.v1.api.customer.serializer import ContactWebhookSerializer
from apps.v1.api.request.models.model import Requests
from apps.v1.api.request.serializer import RequestSerializer
from apps.v1.api.suppliers.models.model import ProductSupplierMapping
from apps.v1.api.logistic.models.model import Logistic
from apps.v1.api.auth.models.model import Users, Modules
from apps.v1.api.auth.models.attribute import Action
from apps.v1.api.auth.serializer import UserWebhookSerializer
from apps.v1.api.request.models.model import RequestCustomersMapping
from apps.v1.api.bitrix.models.methods import BitrixWebhookMethods
from apps.v1.api.bitrix.serializer import BitrixFieldMappingSerializer
from core.azure.azure_blob import AzureBlobService
from config.env_config import get_settings

import asyncio
import aiohttp
import mimetypes
import re
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)
settings = get_settings()


class WebhookDataService:
    """Service to handle webhook data operations (insert, update, delete) for all tables."""

    # Cache for nonexistent columns per table (model columns that don't exist in DB)
    _nonexistent_columns_cache: Dict[str, Set[str]] = {}

    # Table name to model mapping
    TABLE_MODEL_MAP: Dict[str, Type] = {
        "product": Products,
        "products": Products,
        "company": Suppliers,  # Bitrix companies map to suppliers table
        "supplier": Suppliers,
        "suppliers": Suppliers,
        "customer": Customers,
        "customers": Customers,
        "request": Requests,
        "requests": Requests,
        "deal": Requests,  # Bitrix deals map to requests table
        "deals": Requests,
        "logistic": Logistic,
        "category": Categories,
        "categories": Categories,
        "user": Users,
        "users": Users,
    }

    # Table name to serializer mapping
    # Note: Some tables may not have serializers yet - service handles this gracefully
    TABLE_SERIALIZER_MAP: Dict[str, Any] = {
        "product": ProductSerializer,
        "products": ProductSerializer,
        "company": SupplierSerializer,  # Bitrix companies use supplier serializer
        "supplier": SupplierSerializer,
        "suppliers": SupplierSerializer,
        "category": CategorySerializer,
        "categories": CategorySerializer,
        "request": RequestSerializer,
        "requests": RequestSerializer,
        "deal": RequestSerializer,  # Bitrix deals use request serializer
        "deals": RequestSerializer,
        "user": UserWebhookSerializer,
        "users": UserWebhookSerializer,
        # Note: "contact" and "contacts" serializers are kept for backward compatibility
        # but contacts are now routed to "customers" or "suppliers" based on company_type
        # (handled in bitrix_webhook_service.py), so these may not be used
        "contact": ContactWebhookSerializer,
        "contacts": ContactWebhookSerializer,
        # Customer serializers can be added when available
        # "customer": CustomerSerializer,
    }

    # Document fields mapping - normalized field names (lowercase, underscores)
    # These are the normalized names that will match after field name normalization
    DOCUMENT_FIELDS_MAP = {
        "product": [
            "factory_logo", "artwork", "background_image", "link_to_artwork_files", 
            "carton_artwork", "technical_data_sheet", "primary_packing_artwork", 
            "secondary_packing_artwork", "keylines", "documents_from_factory",
            "product_artwork", "photo_of_primary_packing", "photo_of_secondary_packing",
            "primary_packing_artwork", "secondary_packing_artwork", "product_keylines",
            "specification", "carton_artwork", "photo_of_primary_packing", "photo_of_secondary_packing",
            "technical_data_sheet", "primary_packing_artwork", "secondary_packing_artwork"
        ],
        "supplier": ["logo", "certificates", "factory_certificates"],
        "request": ["shipping_documents"],
    }
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name to match DOCUMENT_FIELDS_MAP format."""
        # Convert to lowercase and replace spaces/special chars with underscores
        normalized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name.lower())
        # Remove multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        # Remove leading/trailing underscores
        return normalized.strip('_')

    def __init__(self):
        """Initialize webhook data service."""
        logger.debug("WebhookDataService initialized")
        self.azure_blob_service = AzureBlobService()
        self._doc_session: Optional[aiohttp.ClientSession] = None
        self._doc_cookies = self._build_bitrix_cookies()

    def _get_model(self, table_name: str):
        """Get model class for table name."""
        model = self.TABLE_MODEL_MAP.get(table_name.lower())
        if not model:
            raise ValueError(f"Unsupported table: {table_name}")
        return model

    def _get_serializer(self, table_name: str):
        """Get serializer class for table name."""
        serializer_class = self.TABLE_SERIALIZER_MAP.get(table_name.lower())
        if not serializer_class:
            logger.warning(f"No serializer found for table: {table_name}, using raw data")
            return None
        return serializer_class()

    async def _get_existing_db_columns(self, db: AsyncSession, table_name: str) -> set:
        """Get existing database columns for a table."""
        try:
            model = self._get_model(table_name)
            actual_table_name = model.__tablename__
            return await BitrixWebhookMethods.get_existing_db_columns(db, actual_table_name)
        except Exception as e:
            logger.error(f"Could not query database columns for {table_name}: {e}", exc_info=True)
            model = self._get_model(table_name)
            return {col.name for col in model.__table__.columns}
    
    async def _get_nonexistent_columns(self, db: AsyncSession, table_name: str) -> Set[str]:
        """
        Get columns that exist in the model but not in the database.
        Uses caching to avoid repeated database queries.
        """
        cache_key = table_name.lower()
        
        # Return cached value if available
        if cache_key in self._nonexistent_columns_cache:
            return self._nonexistent_columns_cache[cache_key]
        
        try:
            model = self._get_model(table_name)
            actual_table_name = model.__tablename__
            
            # Get nonexistent columns by comparing model with database
            nonexistent = await BitrixWebhookMethods.get_nonexistent_model_columns(
                db, model, actual_table_name
            )
            
            # No known problematic columns - allow all columns
            known_problematic = set()
            nonexistent = nonexistent.union(known_problematic)
            
            # Cache the result
            self._nonexistent_columns_cache[cache_key] = nonexistent
            
            if nonexistent:
                logger.info(
                    f"Cached {len(nonexistent)} nonexistent columns for {table_name}: {nonexistent}"
                )
            
            return nonexistent
        except Exception as e:
            logger.error(f"Could not get nonexistent columns for {table_name}: {e}", exc_info=True)
            # Return empty set - no columns are excluded
            return set()
    
    def _filter_nonexistent_columns(
        self, data: Dict[str, Any], existing_columns: set, known_nonexistent: Set[str] = None
    ) -> Dict[str, Any]:
        """
        Filter out columns that don't exist in the database.
        
        Args:
            data: Data dictionary to filter
            existing_columns: Set of columns that exist in database
            known_nonexistent: Additional columns to exclude (optional)
        
        Returns:
            Filtered data dictionary
        """
        known_nonexistent = known_nonexistent or set()
        filtered_data, _ = BitrixWebhookMethods.filter_nonexistent_columns(
            data, existing_columns, known_nonexistent
        )
        return filtered_data
    
    def _remove_nonexistent_columns(
        self, data: Dict[str, Any], known_nonexistent: Set[str] = None
    ) -> Dict[str, Any]:
        """
        Remove known nonexistent columns from data.
        
        Args:
            data: Data dictionary to filter
            known_nonexistent: Set of columns to exclude (optional)
        
        Returns:
            Filtered data dictionary
        """
        known_nonexistent = known_nonexistent or set()
        return BitrixWebhookMethods.remove_nonexistent_columns(data, known_nonexistent)
    
    async def _handle_mapping_safely(
        self, db: AsyncSession, table_name: str, mapping: Optional[List[Dict[str, Any]]], record_id: int
    ) -> None:
        """
        Safely handle mapping data with error handling.
        The mapping handler handles errors internally and continues with other mappings.
        """
        if not mapping:
            return
        
        try:
            await self._handle_mapping(db, table_name, mapping, record_id)
        except Exception as mapping_error:
            logger.error(f"Unexpected error in mapping handler for {table_name} (ID: {record_id}): {mapping_error}", exc_info=True)
    
    async def _regenerate_and_update_deal_id(
        self, db: AsyncSession, table_name: str, request_id: int, data: Dict[str, Any], 
        bitrix_id_value: Optional[str] = None, actual_table_name: Optional[str] = None
    ) -> None:
        """Regenerate deal_id for requests table and update it in the database."""
        if table_name.lower() not in ["request", "requests", "deal", "deals"]:
            return
        
        try:
            updated_deal_id = await BitrixWebhookMethods.generate_deal_id(data, db=db, request_id=request_id)
            if not updated_deal_id:
                logger.warning(f"Generated empty deal_id for request {request_id}")
                return
            
            # Check if deal_id already exists and keep appending unique suffixes until we get a unique one
            # Note: generate_deal_id already appends a unique suffix, so we check the full deal_id first
            max_attempts = 10
            attempt = 0
            original_deal_id = updated_deal_id
            
            # Extract base deal_id by removing the suffix that generate_deal_id added
            # The suffix format is: " - ID:{request_id}" or " - BX:{bitrix_id}" or " - TS:{timestamp}"444444444
            base_deal_id = re.sub(r'\s*-\s*(ID|BX|TS):[^\s-]+$', '', original_deal_id)
            
            while attempt < max_attempts:
                existing = await BitrixWebhookMethods.check_deal_id_exists(db, updated_deal_id, exclude_request_id=request_id)
                
                if not existing:
                    # Found a unique deal_id, break the loop
                    break
                
                # Deal_id exists, append a more unique suffix
                attempt += 1
                
                if attempt == 1:
                    # First attempt: append bitrix_id if available, otherwise use request_id with timestamp
                    if bitrix_id_value:
                        updated_deal_id = f"{base_deal_id} - BX:{bitrix_id_value} - ID:{request_id}"
                    else:
                        timestamp = int(time.time() * 1000) % 1000000  # 6 digits
                        updated_deal_id = f"{base_deal_id} - ID:{request_id} - T{timestamp}"
                else:
                    # Subsequent attempts: append attempt number and timestamp
                    timestamp = int(time.time() * 1000) % 1000000  # 6 digits
                    updated_deal_id = f"{base_deal_id} - ID:{request_id} - #{attempt} - T{timestamp}"
                
                logger.info(f"Deal_id exists, trying unique variant (attempt {attempt}): {updated_deal_id}")
            
            if attempt >= max_attempts:
                # If we still couldn't find a unique deal_id after max attempts, use a full timestamp-based one
                timestamp = int(time.time() * 1000)
                updated_deal_id = f"{base_deal_id} - ID:{request_id} - TS:{timestamp}"
                logger.warning(f"Could not find unique deal_id after {max_attempts} attempts, using timestamp-based: {updated_deal_id}")
            
            # Final check before updating - if it still exists, use a guaranteed unique timestamp
            final_check = await BitrixWebhookMethods.check_deal_id_exists(db, updated_deal_id, exclude_request_id=request_id)
            if final_check:
                timestamp = int(time.time() * 1000)
                updated_deal_id = f"{base_deal_id} - ID:{request_id} - TS:{timestamp}"
                logger.warning(f"Deal_id still exists after all attempts, using guaranteed unique timestamp: {updated_deal_id}")
            
            table = actual_table_name or "requests"
            await BitrixWebhookMethods.update_deal_id(db, request_id, updated_deal_id, table)
            logger.info(f"Updated deal_id for request {request_id}: {updated_deal_id}")
        except Exception as e:
            logger.warning(f"Could not regenerate deal_id for request {request_id}: {e}")

    async def _map_bitrix_user_ids_to_db_ids(
        self, db: AsyncSession, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map Bitrix user IDs to database user IDs for request fields.
        - Maps responsible_person (Bitrix ID) to assigned_by (user ID)
        - Maps observer_bitrixids (array of Bitrix IDs) to observer_ids (array of user IDs)
        - Also handles assigned_by if it's already set but contains a Bitrix ID
        - Prevents duplicate user IDs in observer_ids
        """
        # Helper function to convert value to int (handles both string and int)
        def convert_to_int(value: Any) -> Optional[int]:
            """Convert a value to int, handling strings and integers."""
            if value is None:
                return None
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                try:
                    return int(value.strip())
                except (ValueError, TypeError):
                    return None
            # Try to convert other types
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
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
            assigned_by_int = convert_to_int(assigned_by_value)
            
            if assigned_by_int is not None:
                # Find user in users table where bitrix_id = assigned_by_value, get their database id
                resolved_id = await resolve_user_id(assigned_by_int)
                if resolved_id:
                    # Always update assigned_by with the resolved database user ID
                    data["assigned_by"] = resolved_id
                    if resolved_id != assigned_by_int:
                        logger.info(f"Mapped assigned_by Bitrix ID {assigned_by_int} to user ID {resolved_id} (found user with bitrix_id={assigned_by_int} has database id={resolved_id})")
                    else:
                        logger.debug(f"assigned_by {assigned_by_int} is already a valid database user ID")
                else:
                    # User not found in users table, remove assigned_by to avoid FK constraint error
                    logger.warning(f"Could not find user in users table with bitrix_id={assigned_by_int} for assigned_by. Removing to avoid FK constraint error.")
                    data.pop("assigned_by", None)
            else:
                logger.warning(f"Could not convert assigned_by '{assigned_by_value}' to integer. Removing to avoid FK constraint error.")
                data.pop("assigned_by", None)
        
        # Map responsible_person to assigned_by (only if assigned_by is not already set)
        # Check both "responsible_person" (after field mapping) and "Responsible_person" (before field mapping)
        responsible_person_value = None
        if "responsible_person" in data and data["responsible_person"]:
            responsible_person_value = data["responsible_person"]
        elif "Responsible_person" in data and data["Responsible_person"]:
            responsible_person_value = data["Responsible_person"]
        elif "ASSIGNED_BY_ID" in data and data["ASSIGNED_BY_ID"]:
            responsible_person_value = data["ASSIGNED_BY_ID"]
        
        if responsible_person_value and "assigned_by" not in data:
            bitrix_id_raw = responsible_person_value
            try:
                # Convert to int if it's a string (e.g., "218" -> 218)
                bitrix_id = convert_to_int(bitrix_id_raw)
                
                if bitrix_id is not None:
                    # Find user in users table where bitrix_id = 218, get their database id (e.g., 5)
                    resolved_id = await resolve_user_id(bitrix_id)
                    if resolved_id:
                        # Store the database user id (e.g., 5) in assigned_by column
                        data["assigned_by"] = resolved_id
                        logger.info(f"Mapped responsible_person Bitrix ID {bitrix_id} to assigned_by user ID {resolved_id} (found user with bitrix_id={bitrix_id} has database id={resolved_id})")
                    else:
                        # User not found in users table with this bitrix_id, don't set assigned_by to avoid FK constraint error
                        logger.warning(f"Could not find user in users table with bitrix_id={bitrix_id} for assigned_by mapping. Skipping assigned_by.")
                else:
                    logger.warning(f"Could not convert responsible_person '{bitrix_id_raw}' to integer. Skipping assigned_by mapping.")
            except Exception as e:
                logger.error(f"Error mapping responsible_person to assigned_by: {e}")
        
        # Map observer_bitrixids to observer_ids
        if "observer_bitrixids" in data and data["observer_bitrixids"]:
            observer_bitrixids = data["observer_bitrixids"]
            observer_ids_set = set()  # Use set to prevent duplicates
            
            # Handle different input formats
            if isinstance(observer_bitrixids, str):
                # Try to parse as JSON
                try:
                    observer_bitrixids = json.loads(observer_bitrixids)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse observer_bitrixids as JSON: {observer_bitrixids}")
                    observer_bitrixids = []
            
            if isinstance(observer_bitrixids, list):
                for bitrix_id_raw in observer_bitrixids:
                    if not bitrix_id_raw:
                        continue
                    try:
                        # Convert to int (handles both string "218" and int 218)
                        bitrix_id = convert_to_int(bitrix_id_raw)
                        
                        if bitrix_id is not None:
                            # Try to resolve user ID (Bitrix ID or database ID)
                            resolved_id = await resolve_user_id(bitrix_id)
                            if resolved_id:
                                # Add to set to prevent duplicates
                                observer_ids_set.add(resolved_id)
                                if resolved_id != bitrix_id:
                                    logger.debug(f"Mapped observer Bitrix ID {bitrix_id} to user ID {resolved_id}")
                            else:
                                logger.warning(f"Could not find user with ID/Bitrix ID {bitrix_id} for observer_ids mapping")
                        else:
                            logger.warning(f"Could not convert observer Bitrix ID '{bitrix_id_raw}' to integer. Skipping.")
                    except Exception as e:
                        logger.error(f"Error mapping observer Bitrix ID {bitrix_id_raw} to user ID: {e}")
            
            # Convert set back to list (preserving order by converting to sorted list)
            observer_ids = sorted(list(observer_ids_set)) if observer_ids_set else []
            data["observer_ids"] = observer_ids if observer_ids else None
            logger.info(f"Mapped {len(observer_ids)} unique observer Bitrix IDs to user IDs (removed duplicates if any)")
        
        return data

    def _normalize_numeric_value(self, value: Any, field_name: str) -> Any:
        """Normalize numeric value to proper type (int/float) or None."""
        if value is None:
            return None
        
        # Float fields
        float_fields = {"freight_charges", "total", "tax_rate", "advance_payment"}
        # Integer fields
        int_fields = {
            "probability", "lead_rank", "contact_id", "estimate_id", "moved_by_id",
            "repeat_sale_segment_id", "last_activity_by", "loaded_container_quantity",
            "week_commitment", "estimated_volume", "created_by", "modified_by"
        }
        
        # Skip normalization if field is not numeric
        if field_name not in float_fields and field_name not in int_fields:
            return value
        
        # Handle empty strings
        if isinstance(value, str) and value.strip() == "":
            return None
        
        # Handle boolean strings and common non-numeric values
        if isinstance(value, str):
            value_lower = value.lower().strip()
            # Handle boolean-like strings
            if value_lower in ("false", "f", "no", "n", "0", "0.0", ""):
                return 0.0 if field_name in float_fields else 0
            if value_lower in ("true", "t", "yes", "y", "1", "1.0"):
                return 1.0 if field_name in float_fields else 1
            
            # Try to convert string to numeric
            try:
                if field_name in float_fields:
                    return float(value)
                elif field_name in int_fields:
                    return int(float(value))  # Convert via float to handle "1.0" -> 1
            except (ValueError, TypeError):
                logger.warning(f"Could not convert '{value}' to numeric for field '{field_name}', setting to None")
                return None
        
        # Handle boolean values
        if isinstance(value, bool):
            return float(value) if field_name in float_fields else int(value)
        
        # Already numeric - ensure correct type
        if isinstance(value, (int, float)):
            if field_name in float_fields:
                return float(value)
            elif field_name in int_fields:
                return int(value)
        
        # For any other type that shouldn't be in numeric field, return None
        logger.warning(f"Unexpected type '{type(value).__name__}' for numeric field '{field_name}', setting to None")
        return None

    def _normalize_datetime_value(self, value: Any, field_name: str) -> Any:
        """
        Normalize datetime value to proper datetime object or None.
        Handles various date string formats including DD.MM.YYYY, YYYY-MM-DD, ISO format, etc.
        """
        if value is None:
            return None
        
        # Already a datetime object
        if isinstance(value, datetime):
            return value
        
        # Handle empty strings
        if isinstance(value, str) and value.strip() == "":
            return None
        
        # Handle string values - try to parse various formats
        if isinstance(value, str):
            value = value.strip()
            
            # Skip invalid date strings
            if value in ("0000-00-00 00:00:00", "0000-00-00", ""):
                return None
            
            try:
                # Try ISO format first (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
                if "+" in value or value.endswith("Z"):
                    # ISO format with timezone
                    clean_value = value.split("+")[0].split("Z")[0]
                    if "." in clean_value:
                        clean_value = clean_value.split(".")[0]
                    return datetime.fromisoformat(clean_value)
                
                # Try ISO format without timezone
                if "T" in value:
                    return datetime.fromisoformat(value.split(".")[0] if "." in value else value)
                
                # Try DD.MM.YYYY format (e.g., "02.01.2026")
                if "." in value and len(value.split(".")) == 3:
                    parts = value.split(".")
                    if len(parts[0]) <= 2 and len(parts[1]) <= 2 and len(parts[2]) == 4:
                        # DD.MM.YYYY format
                        day, month, year = map(int, parts)
                        return datetime(year, month, day)
                
                # Try YYYY-MM-DD format
                if "-" in value and len(value.split("-")) == 3:
                    parts = value.split("-")
                    if len(parts[0]) == 4:  # YYYY-MM-DD
                        return datetime.fromisoformat(value)
                
                # Try other common formats
                # DD/MM/YYYY
                if "/" in value and len(value.split("/")) == 3:
                    parts = value.split("/")
                    if len(parts[0]) <= 2 and len(parts[1]) <= 2 and len(parts[2]) == 4:
                        day, month, year = map(int, parts)
                        return datetime(year, month, day)
                
                # Try ISO format as fallback
                return datetime.fromisoformat(value)
                
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Could not parse datetime string '{value}' for field '{field_name}': {e}. Setting to None.")
                return None
        
        # For any other type, return None
        logger.warning(f"Unexpected type '{type(value).__name__}' for datetime field '{field_name}', setting to None")
        return None

    def _map_bitrix_to_db_fields(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Bitrix field names to database column names.
        Also filters out fields that don't exist in the database schema.
        """
        model = self._get_model(table_name)
        
        # Get all valid column names from the model
        valid_columns = {col.name for col in model.__table__.columns}
        
        # Get excluded columns from serializer
        excluded_columns = BitrixFieldMappingSerializer.EXCLUDED_COLUMNS
        
        # Filter out metadata fields using serializer
        filtered_data = {k: v for k, v in data.items() if not BitrixFieldMappingSerializer.is_metadata_field(k)}
        
        # Process ID field first
        mapped_data = {}
        if "ID" in filtered_data and "bitrix_id" not in mapped_data:
            mapped_data["bitrix_id"] = str(filtered_data["ID"]) if filtered_data["ID"] else None
        
        # Process remaining fields using dict comprehension and map
        def process_field(item):
            bitrix_key, value = item
            if bitrix_key == "ID":
                return None  # Already processed
            
            # Map field name using serializer
            db_key = BitrixFieldMappingSerializer.get_db_field_name(bitrix_key)
            
            # Handle email -> email_ids conversion
            if bitrix_key == "email" and table_name.lower() in ["contact", "contacts", "customer", "customers"]:
                if "email_ids" in valid_columns:
                    if value:
                        mapped_data["email_ids"] = value if isinstance(value, list) else [str(value)]
                    else:
                        mapped_data["email_ids"] = []
                    return None
            
            # Check if column is valid
            if db_key not in valid_columns or db_key in excluded_columns:
                if db_key in excluded_columns:
                    logger.debug(f"Excluding field '{bitrix_key}' (mapped to '{db_key}') - column not yet in database")
                else:
                    logger.debug(f"Skipping field '{bitrix_key}' (mapped to '{db_key}') - not in database schema")
                return None
            
            # Normalize numeric values
            value = self._normalize_numeric_value(value, db_key)
            
            # Convert boolean values using serializer
            if BitrixFieldMappingSerializer.is_boolean_field(db_key):
                return (db_key, BitrixFieldMappingSerializer.convert_boolean_value(value))
            
            return (db_key, value)
        
        # Process all fields
        processed_fields = filter(None, map(process_field, filtered_data.items()))
        mapped_data.update(dict(processed_fields))
        
        return mapped_data

    async def _handle_mapping(
        self, db: AsyncSession, table_name: str, mapping_data: List[Dict[str, Any]], record_id: int
    ) -> None:
        """
        Handle mapping data (bridge tables).
        Mapping data is always in list format.
        """
        if not mapping_data:
            return

        logger.info(f"Processing mapping data for {table_name} (ID: {record_id})")
        logger.debug(f"Mapping data: {mapping_data}")

        for mapping_item in mapping_data:
            mapping_table = mapping_item.get("table")
            mapping_values = mapping_item.get("data", {})
            
            logger.info(f"Processing mapping: {mapping_table} for {table_name} (ID: {record_id})")
            
            # Handle logistic table (one-to-one with product)
            if mapping_table == "logistic":
                try:
                    # Always use record_id (database ID) for product_id, not Bitrix ID
                    # record_id is the database ID of the product that was just updated/inserted
                    product_db_id = record_id
                    
                    if not product_db_id:
                        logger.warning(f"Missing product database ID (record_id) for logistic mapping, skipping")
                        continue
                    
                    # Check if logistic record already exists for this product
                    # Use raw SQL to check existence first to avoid JSON deserialization issues
                    raw_stmt = text("SELECT id FROM logistic WHERE product_id = :product_id LIMIT 1")
                    raw_result = await db.execute(raw_stmt, {"product_id": product_db_id})
                    row = raw_result.fetchone()
                    existing_logistic_id = row[0] if row else None
                    
                    # If record exists, try to load it (may fail if JSON is corrupted)
                    existing_logistic = None
                    if existing_logistic_id:
                        try:
                            stmt = select(Logistic).where(Logistic.id == existing_logistic_id)
                            result = await db.execute(stmt)
                            existing_logistic = result.scalar_one_or_none()
                        except Exception as json_error:
                            # If JSON deserialization fails, we'll update using raw SQL
                            logger.warning(f"JSON deserialization error when loading logistic record {existing_logistic_id}, will update using raw SQL: {json_error}")
                            existing_logistic = None  # Will use raw SQL update
                    
                    # Prepare logistic data (remove product_id from data as we'll use record_id)
                    logistic_data = {k: v for k, v in mapping_values.items() if k != "product_id"}
                    
                    if existing_logistic:
                        # Update existing logistic record using ORM
                        for key, value in logistic_data.items():
                            if hasattr(existing_logistic, key) and value is not None:
                                setattr(existing_logistic, key, value)
                        logger.info(f"Updated logistic record for product_id (database): {product_db_id}")
                    elif existing_logistic_id:
                        # Record exists but JSON is corrupted, update using raw SQL
                        logger.info(f"Updating logistic record {existing_logistic_id} using raw SQL due to JSON corruption")
                        update_fields = []
                        update_params = {"logistic_id": existing_logistic_id}
                        
                        for key, value in logistic_data.items():
                            if value is not None:
                                if key == "loading_quantities":
                                    # Handle JSON field specially
                                    import json as json_lib
                                    if isinstance(value, (list, dict)):
                                        json_value = json_lib.dumps(value)
                                    else:
                                        json_value = json_lib.dumps(value) if value else None
                                    update_fields.append(f"{key} = :{key}")
                                    update_params[key] = json_value
                                else:
                                    update_fields.append(f"{key} = :{key}")
                                    update_params[key] = value
                        
                        if update_fields:
                            update_sql = text(f"UPDATE logistic SET {', '.join(update_fields)} WHERE id = :logistic_id")
                            await db.execute(update_sql, update_params)
                            logger.info(f"Updated logistic record {existing_logistic_id} using raw SQL")
                    else:
                        # Create new logistic record using database product_id
                        logistic_data["product_id"] = product_db_id
                        new_logistic = Logistic(**logistic_data)
                        db.add(new_logistic)
                        logger.info(f"Created logistic record for product_id (database): {product_db_id}")
                        
                except Exception as exc:
                    logger.error(f"Error handling logistic mapping: {exc}", exc_info=True)
                    # Don't rollback here - let the parent transaction handle it
                    # Re-raise to let parent handle rollback and fail the whole operation
                    raise
            
            # Handle product_suppliers bridge table (many-to-many)
            elif mapping_table == "product_suppliers":
                try:
                    # Determine context based on table_name
                    # When called from product insert, record_id is the product's database ID
                    # When called from supplier insert, record_id is the supplier's database ID
                    product_db_id = None
                    supplier_db_id = None
                    
                    # Use table_name to determine context
                    if table_name.lower() in ["product", "products"]:
                        # This is from product processing - record_id is product_id
                        product_db_id = record_id
                        supplier_id = mapping_values.get("supplier_id")
                        
                        if not supplier_id:
                            logger.error(f"Missing supplier_id in mapping_values for product_suppliers mapping. Cannot create mapping without supplier_id.")
                            # Don't skip - try to continue with other mappings or log error
                            continue
                        
                        supplier_stmt = select(Suppliers.id).where(Suppliers.bitrix_id == str(supplier_id))
                        supplier_result = await db.execute(supplier_stmt)
                        supplier_db_id = supplier_result.scalar_one_or_none()
                        
                        # If not found by bitrix_id, try as database ID (fallback)
                        if not supplier_db_id:
                            supplier_stmt = select(Suppliers.id).where(Suppliers.id == supplier_id)
                            supplier_result = await db.execute(supplier_stmt)
                            supplier_db_id = supplier_result.scalar_one_or_none()
                        
                        # Validate supplier exists before proceeding
                        if not supplier_db_id:
                            logger.error(f"Supplier with Bitrix ID or database ID {supplier_id} not found in suppliers table. Cannot create product_suppliers mapping. Please ensure supplier exists first.")
                            # Try to find by name or other fields as last resort
                            # For now, log error and continue - but this should be addressed
                            continue
                    
                    elif table_name.lower() in ["supplier", "suppliers", "company", "companies"]:
                        # This is from supplier processing - record_id is supplier_id
                        supplier_db_id = record_id
                        product_id = mapping_values.get("product_id")
                        
                        if not product_id:
                            logger.error(f"Missing product_id in mapping_values for product_suppliers mapping. Cannot create mapping without product_id.")
                            continue
                    
                        product_stmt = select(Products.id).where(Products.bitrix_id == str(product_id))
                        product_result = await db.execute(product_stmt)
                        product_db_id = product_result.scalar_one_or_none()
                        
                        # If not found by bitrix_id, try as database ID (fallback)
                        if not product_db_id:
                            product_stmt = select(Products.id).where(Products.id == product_id)
                            product_result = await db.execute(product_stmt)
                            product_db_id = product_result.scalar_one_or_none()
                        
                        # Validate product exists before proceeding
                        if not product_db_id:
                            logger.error(f"Product with Bitrix ID or database ID {product_id} not found in products table. Cannot create product_suppliers mapping. Please ensure product exists first.")
                            continue
                    else:
                        logger.warning(f"Unknown table_name '{table_name}' for product_suppliers mapping, skipping")
                        continue
                    
                    if not supplier_db_id or not product_db_id:
                        logger.error(f"Missing supplier_id ({supplier_db_id}) or product_id ({product_db_id}) for product_suppliers mapping. Cannot create mapping.")
                        continue
                    
                    supplier_check = await db.execute(
                        select(Suppliers.id).where(Suppliers.id == supplier_db_id)
                    )
                    if not supplier_check.scalar_one_or_none():
                        logger.error(f"Supplier {supplier_db_id} does not exist in suppliers table. Cannot create product_suppliers mapping.")
                        continue
                    
                    product_check = await db.execute(
                        select(Products.id).where(Products.id == product_db_id)
                    )
                    if not product_check.scalar_one_or_none():
                        logger.error(f"Product {product_db_id} does not exist in products table. Cannot create product_suppliers mapping.")
                        continue
                    
                    existing_mapping = await db.execute(
                        select(ProductSupplierMapping).where(
                            ProductSupplierMapping.supplier_id == supplier_db_id,
                            ProductSupplierMapping.product_id == product_db_id
                        )
                    )
                    existing = existing_mapping.scalar_one_or_none()
                    
                    # Get name from mapping_values, default to empty string if None
                    mapping_name = mapping_values.get("name") or ""
                    
                    if existing:
                        # Update existing mapping
                        existing.name = mapping_name
                        logger.info(f"Updated ProductSupplierMapping for supplier_id={supplier_db_id}, product_id={product_db_id}")
                    else:
                        # Create new mapping
                        new_mapping = ProductSupplierMapping(
                            supplier_id=supplier_db_id,
                            product_id=product_db_id,
                            name=mapping_name
                        )
                        db.add(new_mapping)
                        logger.info(f"Created ProductSupplierMapping for supplier_id={supplier_db_id}, product_id={product_db_id}")
                        
                except Exception as exc:
                    logger.error(f"Error handling product_suppliers mapping: {exc}", exc_info=True)
                    raise
            
            # Handle request_customers bridge table (many-to-many)
            elif mapping_table == "request_customers":
                try:
                    # record_id is the request database ID (when called from request/deal processing)
                    # OR customer database ID (when called from customer processing)
                    request_id = record_id  # Default: assume record_id is request_id
                    customer_id = None
                    
                    # Check if mapping_values contains request_id (from customer processing)
                    if "request_id" in mapping_values:
                        # This is from customer processing - record_id is customer_id
                        customer_id = record_id
                        request_id = mapping_values.get("request_id")
                        
                        if isinstance(request_id, str) or (isinstance(request_id, int) and request_id > 10000):
                            # Likely a Bitrix ID, try to find database request_id
                            request_stmt = select(Requests.id).where(Requests.bitrix_id == str(request_id))
                            request_result = await db.execute(request_stmt)
                            db_request_id = request_result.scalar_one_or_none()
                            if db_request_id:
                                request_id = db_request_id
                            else:
                                logger.warning(f"Request with Bitrix ID {request_id} not found, skipping request_customers mapping")
                                continue
                    # Check if mapping_values contains company_bitrix_id (from deal processing)
                    elif "company_bitrix_id" in mapping_values:
                        # This is from deal processing - record_id is request_id
                        request_id = record_id
                        company_bitrix_id = mapping_values.get("company_bitrix_id")
                        
                        # Find customer database ID from company Bitrix ID
                        # Handle case where bitrix_id column might not exist in database
                        customer_id = None
                        try:
                            customer_stmt = select(Customers.id).where(Customers.bitrix_id == str(company_bitrix_id))
                            customer_result = await db.execute(customer_stmt)
                            customer_id = customer_result.scalar_one_or_none()
                        except Exception as e:
                            # Check if error is due to missing column
                            error_str = str(e).lower()
                            if "unknown column" in error_str or "bitrix_id" in error_str:
                                logger.warning(f"Customer table does not have bitrix_id column. Cannot lookup customer by Bitrix ID {company_bitrix_id}. Skipping request_customers mapping.")
                                customer_id = None
                            else:
                                # Other error - log and skip
                                logger.warning(f"Error looking up customer by Bitrix ID {company_bitrix_id}: {e}. Skipping request_customers mapping.")
                                customer_id = None
                        
                        if not customer_id:
                            logger.error(f"Customer with Bitrix ID {company_bitrix_id} not found. Cannot create request_customers mapping. Please ensure customer exists first.")
                            continue
                    else:
                        logger.error(f"Missing request_id or company_bitrix_id for request_customers mapping. Cannot create mapping.")
                        continue
                    
                    if not request_id or not customer_id:
                        logger.error(f"Missing request_id ({request_id}) or customer_id ({customer_id}) for request_customers mapping. Cannot create mapping.")
                        continue
                    
                    existing_mapping = await db.execute(
                        select(RequestCustomersMapping).where(
                            RequestCustomersMapping.customer_id == customer_id,
                            RequestCustomersMapping.request_id == request_id
                        )
                    )
                    existing = existing_mapping.scalar_one_or_none()
                    
                    if existing:
                        logger.info(f"RequestCustomersMapping already exists for customer_id={customer_id}, request_id={request_id}")
                    else:
                        # Create new mapping
                        new_mapping = RequestCustomersMapping(
                            customer_id=customer_id,
                            request_id=request_id
                        )
                        db.add(new_mapping)
                        logger.info(f"Created RequestCustomersMapping for customer_id={customer_id}, request_id={request_id}")
                        
                except Exception as exc:
                    logger.error(f"Error handling request_customers mapping: {exc}", exc_info=True)
                    raise
            
            # Handle request_products bridge table (many-to-many)
            elif mapping_table == "request_products":
                try:
                    # record_id is the request database ID
                    request_db_id = record_id
                    product_id = mapping_values.get("product_id")
                    
                    if not request_db_id or not product_id:
                        logger.error(f"Missing request_id ({request_db_id}) or product_id ({product_id}) for request_products mapping. Cannot create mapping.")
                        continue
                    
                    # Use raw SQL to avoid autoflush issues
                    
                    # Always try to look up product by bitrix_id first (since mapping data contains Bitrix IDs)
                    db_product_id = None
                    
                    # First, try to find by Bitrix ID using raw SQL
                    product_result = await db.execute(
                        text("SELECT id FROM products WHERE bitrix_id = :bitrix_id LIMIT 1"),
                        {"bitrix_id": str(product_id)}
                    )
                    row = product_result.fetchone()
                    if row:
                        db_product_id = row[0]
                    
                    # If not found by Bitrix ID, try as database ID (fallback)
                    if not db_product_id:
                        product_result = await db.execute(
                            text("SELECT id FROM products WHERE id = :product_id LIMIT 1"),
                            {"product_id": product_id}
                        )
                        row = product_result.fetchone()
                        if row:
                            db_product_id = row[0]
                    
                    # Validate product exists before proceeding
                    if not db_product_id:
                        logger.error(f"Product with Bitrix ID or database ID {product_id} not found in products table. Cannot create request_products mapping. Please ensure product exists first.")
                        continue
                    
                    # Use the database product_id
                    product_id = db_product_id
                    
                    # Check if mapping already exists using raw SQL
                    existing_result = await db.execute(
                        text("SELECT id FROM request_products WHERE request_id = :request_id AND product_id = :product_id LIMIT 1"),
                        {"request_id": request_db_id, "product_id": product_id}
                    )
                    existing_row = existing_result.fetchone()
                    
                    if existing_row:
                        logger.info(f"RequestProductsMapping already exists for request_id={request_db_id}, product_id={product_id}")
                    else:
                        # Create new mapping using raw SQL to avoid autoflush issues
                        try:
                            await db.execute(
                                text("INSERT INTO request_products (request_id, product_id, created_at, updated_at) VALUES (:request_id, :product_id, NOW(), NOW())"),
                                {"request_id": request_db_id, "product_id": product_id}
                            )
                            logger.info(f"Created RequestProductsMapping for request_id={request_db_id}, product_id={product_id}")
                        except Exception as insert_error:
                            # Check if it's a foreign key constraint error
                            error_str = str(insert_error)
                            if "foreign key constraint" in error_str.lower() or "1452" in error_str:
                                logger.error(f"Foreign key constraint failed: Product {product_id} does not exist in products table. Cannot create request_products mapping.")
                            else:
                                logger.error(f"Error inserting request_products mapping: {insert_error}")
                            # Continue with other mappings instead of failing
                            continue
                        
                except Exception as exc:
                    logger.error(f"Error handling request_products mapping for request {record_id}: {exc}", exc_info=True)
                    # Don't raise - continue with other mappings to avoid failing entire transaction
                    # The error is logged, and we'll skip this mapping
                    continue
            
            # Handle other bridge tables
            else:
                logger.warning(f"Mapping table '{mapping_table}' not yet implemented. Mapping data: {mapping_values}")
                # Don't skip - log warning but continue processing other mappings
                # This ensures we don't silently skip mapping data
                continue

    async def insert(
        self, db: AsyncSession, table_name: str, data: Dict[str, Any], bitrix_id: Optional[str] = None, mapping: Optional[List[Dict[str, Any]]] = None, _from_update: bool = False
    ) -> Dict[str, Any]:
        """Insert a new record into the specified table."""
        try:
            logger.info(f"Inserting record into {table_name}")
            
            # IMPORTANT: Store original data for document processing (before any mapping/filtering)
            original_data_for_docs = data.copy()
            
            model = self._get_model(table_name)
            serializer = self._get_serializer(table_name)

            # Map Bitrix field names to database column names and filter invalid fields
            mapped_data = self._map_bitrix_to_db_fields(table_name, data)

            # Validate and normalize data using serializer if available
            if serializer:
                try:
                    normalized_data = serializer.load(mapped_data)
                except Exception as serializer_error:
                    logger.warning(f"Serializer failed, using mapped data directly: {serializer_error}")
                    normalized_data = mapped_data.copy()
            else:
                normalized_data = mapped_data.copy()

            # Add bitrix_id if provided and normalize to string for consistent comparison
            if bitrix_id:
                normalized_data["bitrix_id"] = str(bitrix_id)
            
            # Ensure bitrix_id in normalized_data is also a string
            if "bitrix_id" in normalized_data and normalized_data["bitrix_id"]:
                normalized_data["bitrix_id"] = str(normalized_data["bitrix_id"])

            # Remove id if present (auto-generated)
            normalized_data.pop("id", None)

            # Map Bitrix user IDs to database user IDs for requests table
            if table_name.lower() in ["request", "requests", "deal", "deals"]:
                normalized_data = await self._map_bitrix_user_ids_to_db_ids(db, normalized_data)

            # Set default values for required fields
            normalized_data = BitrixWebhookMethods.set_default_values_for_required_fields(table_name, normalized_data, is_insert=True)
            
            # Normalize numeric values before filtering
            float_fields = {"freight_charges", "total", "tax_rate", "advance_payment"}
            int_fields = {
                "probability", "lead_rank", "contact_id", "estimate_id", "moved_by_id",
                "repeat_sale_segment_id", "last_activity_by", "loaded_container_quantity",
                "week_commitment", "estimated_volume", "created_by", "modified_by",
                "item_id_in_data_source"
            }
            numeric_fields = float_fields | int_fields
            for field in numeric_fields:
                if field in normalized_data:
                    normalized_data[field] = self._normalize_numeric_value(normalized_data[field], field)
            
            # Normalize datetime values before filtering (handles DD.MM.YYYY format and others)
            datetime_fields = {
                "start_date", "end_date", "inquiry_date", "cargo_readiness_date", "moved_time", "last_activity_time",
                "production_date", "loading_date", "etd", "eta", "latest_date_of_shipment",
                "lc_expiry_date", "shipping_date", "next_lots_loading_dates", "last_communication_time", "last_contact"
            }
            for field in datetime_fields:
                if field in normalized_data:
                    normalized_data[field] = self._normalize_datetime_value(normalized_data[field], field)
            
            # Get actual database columns and filter out any that don't exist
            existing_columns = await self._get_existing_db_columns(db, table_name)
            
            # Get nonexistent columns (model columns that don't exist in DB)
            nonexistent_columns = await self._get_nonexistent_columns(db, table_name)
            
            # Filter out columns that don't exist in database
            normalized_data = self._filter_nonexistent_columns(
                normalized_data, existing_columns, nonexistent_columns
            )
            
            # Final safety check: remove any known nonexistent columns that might have been added back
            normalized_data = self._remove_nonexistent_columns(normalized_data, nonexistent_columns)
            
            # Check if a record with the same bitrix_id already exists (to prevent duplicates)
            # Skip this check if called from update() to prevent infinite loops
            bitrix_id_val = normalized_data.get("bitrix_id") or bitrix_id
            existing_record_id = None
            
            # Ensure bitrix_id_val is a string for consistent comparison
            if bitrix_id_val:
                bitrix_id_val = str(bitrix_id_val)
            
            logger.info(f"🔍 DUPLICATE CHECK: Checking for existing record with bitrix_id={bitrix_id_val} in table={table_name}, _from_update={_from_update}")
            
            if not _from_update and bitrix_id_val:
                actual_table = model.__tablename__
                from sqlalchemy import text as sql_text_lock
                
                # Multiple checks to catch duplicates:
                # 1. Standard check with FOR UPDATE
                # 2. Fresh check without lock (to see committed data)
                # 3. Check all records with this bitrix_id (to catch any duplicates)
                
                # Check 1: Standard FOR UPDATE check
                lock_check = await db.execute(
                    sql_text_lock(f"SELECT id FROM `{actual_table}` WHERE bitrix_id = :bitrix_id AND (deleted_at IS NULL OR YEAR(deleted_at) = 0) LIMIT 1 FOR UPDATE"),
                    {"bitrix_id": bitrix_id_val}
                )
                lock_row = lock_check.fetchone()
                if lock_row:
                    existing_record_id = lock_row[0]
                    logger.warning(f"⚠️ DUPLICATE CHECK 1: Found existing record id={existing_record_id} with bitrix_id={bitrix_id_val}")
                
                # Check 2: Fresh check (no lock, sees committed data from other transactions)
                if not existing_record_id:
                    fresh_check = await db.execute(
                        sql_text_lock(f"SELECT id FROM `{actual_table}` WHERE bitrix_id = :bitrix_id AND (deleted_at IS NULL OR YEAR(deleted_at) = 0) LIMIT 1"),
                        {"bitrix_id": bitrix_id_val}
                    )
                    fresh_row = fresh_check.fetchone()
                    if fresh_row:
                        existing_record_id = fresh_row[0]
                        logger.warning(f"⚠️ DUPLICATE CHECK 2 (fresh): Found existing record id={existing_record_id} with bitrix_id={bitrix_id_val}")
                
                # Check 3: Check ALL records with this bitrix_id (catch any duplicates)
                all_check = await db.execute(
                    sql_text_lock(f"SELECT id FROM `{actual_table}` WHERE bitrix_id = :bitrix_id AND (deleted_at IS NULL OR YEAR(deleted_at) = 0) ORDER BY id ASC"),
                    {"bitrix_id": bitrix_id_val}
                )
                all_rows = all_check.fetchall()
                if len(all_rows) > 0:
                    existing_ids = [row[0] for row in all_rows]
                    if not existing_record_id:
                        existing_record_id = existing_ids[0]  # Use the first (oldest) record
                    if len(all_rows) > 1:
                        logger.error(f"🚨 DUPLICATE CHECK 3: Found {len(all_rows)} existing records with bitrix_id={bitrix_id_val}: {existing_ids}. This indicates existing duplicates in database!")
                    else:
                        logger.info(f"✅ DUPLICATE CHECK 3: Found 1 existing record id={existing_record_id} with bitrix_id={bitrix_id_val}")
            
            if existing_record_id:
                # Record already exists, update it instead of creating a new one
                logger.warning(f"Record with bitrix_id {bitrix_id_val} already exists (id: {existing_record_id}) in {table_name}. Updating instead of inserting.")
                return await self.update(
                    db=db,
                    table_name=table_name,
                    data=normalized_data,
                    bitrix_id=str(bitrix_id_val),
                    mapping=mapping,
                    _from_insert=True
                )

            # Generate deal_id for requests table if not provided
            # Note: We'll regenerate it after insert with full data, so use a unique placeholder for now
            if table_name.lower() in ["request", "requests", "deal", "deals"]:
                if not normalized_data.get("deal_id"):
                    # Set a unique temporary placeholder - will be regenerated after insert with full data
                    # Use timestamp + bitrix_id to ensure uniqueness
                    unique_suffix = int(time.time() * 1000)  # milliseconds for better uniqueness
                    normalized_data["deal_id"] = f"TEMP-{normalized_data.get('bitrix_id', 'NEW')}-{unique_suffix}"

            # Log the columns that will be used for insert (for debugging)
            logger.debug(f"Creating {table_name} record with columns: {sorted(normalized_data.keys())}")

            # Create new record - catch duplicate key errors
            try:
                new_record = model(**normalized_data)
                db.add(new_record)
                await db.flush()
                record_id = new_record.id
            except Exception as insert_error:
                error_str = str(insert_error).lower()
                
                # Check if it's a duplicate key error - if yes, update instead
                if ("duplicate" in error_str or "1062" in error_str or "unique" in error_str) and bitrix_id_val:
                    logger.warning(f"Duplicate key error during insert for bitrix_id {bitrix_id_val}. Updating instead.")
                    await db.rollback()
                    existing_record_id = await BitrixWebhookMethods.get_record_id_by_bitrix_id(
                        db=db,
                        table_name=table_name,
                        bitrix_id=bitrix_id_val,
                        include_deleted=False
                    )
                    if existing_record_id:
                        return await self.update(
                            db=db,
                            table_name=table_name,
                            data=data,  # Use original data for update
                            bitrix_id=bitrix_id_val,
                            mapping=mapping,
                            _from_insert=True
                        )
                    raise
                
                # Check if it's a column mismatch error (1054 = Unknown column)
                if "Unknown column" in error_str or "1054" in error_str:
                    # Column mismatch - use raw SQL for insert
                    logger.warning(f"Model insert failed due to column mismatch, using raw SQL: {error_str}")
                    
                    # Rollback the failed transaction
                    await db.rollback()
                    
                    # Store original data for document processing in raw SQL path
                    original_data_for_docs_raw = data.copy()
                    
                    # IMPORTANT: Check again for duplicates before raw SQL insert (race condition protection)
                    if bitrix_id_val:
                        existing_record_id = await BitrixWebhookMethods.get_record_id_by_bitrix_id(
                            db=db,
                            table_name=table_name,
                            bitrix_id=str(bitrix_id_val),
                            include_deleted=False
                        )
                        
                        if existing_record_id:
                            # Record was created by another process, update instead
                            logger.warning(f"Record with bitrix_id {bitrix_id_val} found during raw SQL fallback (id: {existing_record_id}). Updating instead.")
                            return await self.update(
                                db=db,
                                table_name=table_name,
                                data=normalized_data,
                                bitrix_id=str(bitrix_id_val),
                                mapping=mapping,
                                _from_insert=True
                            )
                    
                    actual_table_name = model.__tablename__

                    
                    # Get nonexistent columns and ensure they're removed from data
                    nonexistent_columns = await self._get_nonexistent_columns(db, table_name)
                    safe_data = self._remove_nonexistent_columns(normalized_data.copy(), nonexistent_columns)
                    
                    # Get existing columns to double-check
                    existing_columns = await self._get_existing_db_columns(db, table_name)
                    safe_data = self._filter_nonexistent_columns(safe_data, existing_columns, nonexistent_columns)
                    
                    # Remove columns with None values to avoid NULL constraint errors
                    # This allows the database to use default values or skip the column if it's nullable
                    safe_data = {k: v for k, v in safe_data.items() if v is not None}
                    
                    # Build INSERT query manually with only existing columns that have values
                    columns = list(safe_data.keys())
                    if not columns:
                        raise ValueError(f"No valid columns to insert for {actual_table_name}")
                    
                    # Prepare data for SQL binding - serialize JSON fields and handle None values
                    # JSON fields that cannot be null and have default=list in model
                    json_fields_with_default = {
                        "key_instructions_to_ops", "manufacturer", "hashtag", 
                        "shipping_documents", "product_category", "observer_bitrixids", "observer_ids"
                    }
                    
                    # Float fields that need explicit conversion
                    float_fields = {"freight_charges", "total", "tax_rate", "advance_payment"}
                    # Integer fields
                    int_fields = {
                        "probability", "lead_rank", "contact_id", "estimate_id", "moved_by_id",
                        "repeat_sale_segment_id", "last_activity_by", "loaded_container_quantity",
                        "week_commitment", "estimated_volume", "created_by", "modified_by",
                        "item_id_in_data_source"
                    }
                    numeric_fields = float_fields | int_fields
                    
                    # Datetime fields that need normalization
                    datetime_fields = {
                        "start_date", "end_date", "inquiry_date", "cargo_readiness_date", "moved_time", "last_activity_time",
                        "production_date", "loading_date", "etd", "eta", "latest_date_of_shipment",
                        "lc_expiry_date", "shipping_date", "next_lots_loading_dates", "last_communication_time", "last_contact"
                    }
                    
                    sql_params = {}
                    final_columns = []
                    for col in columns:
                        value = safe_data[col]
                        # CRITICAL: Normalize datetime fields FIRST - parse string formats like DD.MM.YYYY
                        if col in datetime_fields:
                            normalized = self._normalize_datetime_value(value, col)
                            sql_params[col] = normalized
                        # CRITICAL: Normalize numeric fields - convert strings to proper types or None
                        elif col in numeric_fields:
                            normalized = self._normalize_numeric_value(value, col)
                            # Skip columns with empty strings converted to normalized to avoid NULL constraint errors
                            continue
                        # Handle JSON fields (lists, dicts) - serialize to JSON string
                        elif isinstance(value, (list, dict)):
                            try:
                                sql_params[col] = json.dumps(value) if value else json.dumps([])
                                final_columns.append(col)
                            except (TypeError, ValueError):
                                # For JSON fields with default=list, use empty list instead of None
                                if col in json_fields_with_default:
                                    sql_params[col] = json.dumps([])
                                    final_columns.append(col)
                                # Skip if None and not in json_fields_with_default
                        # Handle None values for JSON fields with default=list
                        elif value is None and col in json_fields_with_default:
                            sql_params[col] = json.dumps([])
                            final_columns.append(col)
                        # Handle datetime objects - already normalized, use as-is
                        elif isinstance(value, datetime):
                            sql_params[col] = value
                            final_columns.append(col)
                        # Skip None values to avoid NULL constraint errors
                        elif value is None:
                            continue
                        # Handle other types as-is (but double-check for numeric/datetime fields that might have been missed)
                        else:
                            # Safety check: if this looks like it should be datetime, normalize it
                            if col in datetime_fields:
                                sql_params[col] = self._normalize_datetime_value(value, col)
                            # Safety check: if this looks like it should be numeric, normalize it
                            elif col in numeric_fields:
                                sql_params[col] = self._normalize_numeric_value(value, col)
                            else:
                                sql_params[col] = value
                            final_columns.append(col)
                    
                    # Update columns list to only include columns that have values
                    columns = final_columns
                    
                    # CRITICAL: One final check right before raw SQL insert
                    if bitrix_id_val:
                        final_pre_insert_check = await db.execute(
                            sql_text(f"SELECT id FROM `{actual_table_name}` WHERE bitrix_id = :bitrix_id AND (deleted_at IS NULL OR YEAR(deleted_at) = 0) LIMIT 1"),
                            {"bitrix_id": str(bitrix_id_val)}
                        )
                        final_pre_insert_row = final_pre_insert_check.fetchone()
                        if final_pre_insert_row:
                            existing_id = final_pre_insert_row[0]
                            logger.error(f"🚨 PRE-RAW-SQL-INSERT DUPLICATE: Record with bitrix_id {bitrix_id_val} already exists (id: {existing_id}). Updating instead.")
                            return await self.update(
                                db=db,
                                table_name=table_name,
                                data=normalized_data,
                                bitrix_id=str(bitrix_id_val),
                                mapping=mapping,
                                _from_insert=True
                            )
                    
                    placeholders = [f":{col}" for col in columns]
                    insert_sql = sql_text(
                        f"INSERT INTO `{actual_table_name}` (`{'`, `'.join(columns)}`) VALUES ({', '.join(placeholders)})"
                    )
                    
                    try:
                        await db.execute(insert_sql, sql_params)
                        await db.flush()
                    except Exception as raw_sql_error:
                        error_str = str(raw_sql_error).lower()
                        # Check if it's a duplicate key error - if yes, update instead
                        if ("duplicate" in error_str or "1062" in error_str or "unique" in error_str) and bitrix_id_val:
                            logger.warning(f"Duplicate key error during raw SQL insert for bitrix_id {bitrix_id_val}. Updating instead.")
                            await db.rollback()
                            existing_record_id = await BitrixWebhookMethods.get_record_id_by_bitrix_id(
                                db=db,
                                table_name=table_name,
                                bitrix_id=bitrix_id_val,
                                include_deleted=False
                            )
                            if existing_record_id:
                                return await self.update(
                                    db=db,
                                    table_name=table_name,
                                    data=normalized_data,
                                    bitrix_id=bitrix_id_val,
                                    mapping=mapping,
                                    _from_insert=True
                                )
                        raise
                    
                    # Get the inserted record ID
                    id_result = await db.execute(
                        sql_text(f"SELECT id FROM `{actual_table_name}` WHERE bitrix_id = :bitrix_id ORDER BY id DESC LIMIT 1"),
                        {"bitrix_id": safe_data.get("bitrix_id")}
                    )
                    id_row = id_result.fetchone()
                    record_id = id_row[0] if id_row else None
                    
                    if not record_id:
                        raise ValueError(f"Failed to get inserted record ID for {actual_table_name}")
                    
                    # Handle mapping data if provided (before document processing)
                    await self._handle_mapping_safely(db, table_name, mapping, record_id)
                    
                    # Regenerate deal_id for requests table after mappings are handled
                    bitrix_id_val = safe_data.get("bitrix_id") or bitrix_id
                    await self._regenerate_and_update_deal_id(
                        db, table_name, record_id, {}, bitrix_id_val, actual_table_name
                    )
                    
                    logger.info(f"✅ Inserted record in {actual_table_name} (ID: {record_id}) using raw SQL due to column mismatch")
                    # Set new_record to None since we used raw SQL
                    new_record = None
                    
                    # Commit the record first before processing documents (raw SQL path)
                    try:
                        await db.commit()
                        logger.info(f"✅ Successfully committed {table_name} record (ID: {record_id}) to database (raw SQL path)")
                    except Exception as commit_error:
                        await db.rollback()
                        logger.error(f"❌ Failed to commit {table_name} record: {commit_error}")
                        raise
                    
                    # Process documents AFTER commit (raw SQL path)
                    # Use original_data_for_docs_raw to ensure we have all fields before mapping
                    if table_name.lower() in ["product", "products", "supplier", "suppliers", "company", "companies", "request", "requests", "deal", "deals"]:
                        try:
                            logger.info(f"📎 Processing documents for {table_name} (ID: {record_id}) AFTER record commit (raw SQL path)")
                            await self._process_documents(db, table_name, record_id, original_data_for_docs_raw)
                        except Exception as doc_error:
                            logger.error(f"❌ Error processing documents for {table_name} (ID: {record_id}): {doc_error}", exc_info=True)
                            logger.warning(f"   ⚠️ Record was successfully inserted, but document processing failed. Documents can be processed later.")
                # Check if it's a duplicate key error (race condition)
                elif "duplicate" in error_str.lower() or "1062" in error_str or "unique" in error_str.lower():
                    # Another record with the same bitrix_id was inserted concurrently
                    # Check again and update instead
                    logger.warning(f"Duplicate key error during insert (race condition), checking for existing record: {insert_error}")
                    await db.rollback()
                    
                    if bitrix_id_val:
                        # If called from update(), try a fresh query after rollback to find the record
                        if _from_update:
                            logger.warning(f"Duplicate key error when insert() called from update(). Trying fresh query to find record.")
                            # Commit any pending changes and try a fresh query
                            try:
                                await db.commit()
                            except:
                                pass  # Ignore commit errors
                            
                        existing_record_id = await BitrixWebhookMethods.get_record_id_by_bitrix_id(
                            db=db,
                            table_name=table_name,
                            bitrix_id=str(bitrix_id_val),
                            include_deleted=False
                        )
                        
                        if existing_record_id:
                            # Update the existing record instead
                            logger.info(f"Found existing record (id: {existing_record_id}) after duplicate key error. Updating instead.")
                            return await self.update(
                                db=db,
                                table_name=table_name,
                                data=normalized_data,
                                bitrix_id=str(bitrix_id_val),
                                mapping=mapping,
                                _from_insert=True
                            )
                        elif _from_update:
                            # If we still can't find it after fresh query, this is a serious issue
                            logger.error(f"CRITICAL: Duplicate key error but record not found even after fresh query. bitrix_id: {bitrix_id_val}")
                            raise ValueError(f"Duplicate key error for bitrix_id {bitrix_id_val} but record not found. This indicates a database consistency issue.")
                
                # If it's not a duplicate error, re-raise it
                raise

            # Handle mapping data if provided
            await self._handle_mapping_safely(db, table_name, mapping, record_id)
            
            # Regenerate deal_id for requests table after mappings are handled
            bitrix_id_val = normalized_data.get("bitrix_id") or (new_record.bitrix_id if new_record and hasattr(new_record, 'bitrix_id') else None)
            await self._regenerate_and_update_deal_id(
                db, table_name, record_id, {}, bitrix_id_val
            )

            # Create activity log for request insertions (before commit)
            if table_name.lower() in ["request", "requests", "deal", "deals"]:
                try:
                    # Get user_id - try assigned_by first (database ID), then created_by (might be Bitrix ID)
                    user_id = normalized_data.get("assigned_by")
                    if not user_id:
                        # If created_by is provided, try to map it from Bitrix ID to database ID
                        created_by_value = normalized_data.get("created_by")
                        if created_by_value:
                            # Check if it's a Bitrix ID (large number) or database ID
                            if isinstance(created_by_value, int) and created_by_value > 1000:
                                # Likely a Bitrix ID, try to find database user ID
                                user_stmt = select(Users.id).where(Users.bitrix_id == created_by_value).limit(1)
                                user_result = await db.execute(user_stmt)
                                db_user_id = user_result.scalar_one_or_none()
                                user_id = db_user_id if db_user_id else created_by_value
                            else:
                                user_id = created_by_value
                    
                    await BitrixWebhookMethods.create_request_activity_log(
                        db=db,
                        request_id=record_id,
                        action=Action.CREATE,
                        user_id=user_id,
                        description=f"Request created via webhook: {normalized_data.get('name', 'N/A')}",
                        metadata={"bitrix_id": bitrix_id, "source": "webhook"}
                    )
                except Exception as log_error:
                    # Log error but don't fail the insert operation
                    logger.warning(f"Failed to create activity log for request {record_id}: {log_error}")
                
                # Create RequestStageActivity records based on deal_stage
                try:
                    deal_stage = normalized_data.get("deal_stage") or (new_record.deal_stage if hasattr(new_record, 'deal_stage') else None)
                    phase = normalized_data.get("phase") or (new_record.phase.value if hasattr(new_record, 'phase') and new_record.phase else None)
                    current_stage_id = normalized_data.get("current_stage_id") or (new_record.current_stage_id if hasattr(new_record, 'current_stage_id') else None)
                    
                    if deal_stage or current_stage_id:
                        await BitrixWebhookMethods.create_request_stage_activities(
                            db=db,
                            request_id=record_id,
                            deal_stage=deal_stage,
                            phase=phase,
                            current_stage_id=current_stage_id
                        )
                except Exception as stage_error:
                    # Log error but don't fail the insert operation
                    logger.warning(f"Failed to create RequestStageActivity for request {record_id}: {stage_error}")

            # STEP 1: Commit the main record FIRST (products/suppliers/requests)
            # This ensures the record exists in database before processing documents
            try:
                await db.commit()
                logger.info(f"✅ Successfully committed {table_name} record (ID: {record_id}) to database")
            except Exception as commit_error:
                error_str = str(commit_error).lower()
                # Check if it's a duplicate key error during commit
                if ("duplicate" in error_str or "1062" in error_str or "unique" in error_str) and bitrix_id_val:
                    logger.error(f"🚨 DUPLICATE KEY ERROR DURING COMMIT: {commit_error}. Rolling back and updating instead.")
                    await db.rollback()
                    
                    # Find the existing record and update it instead
                    existing_record_id = await BitrixWebhookMethods.get_record_id_by_bitrix_id(
                        db=db,
                        table_name=table_name,
                        bitrix_id=str(bitrix_id_val),
                        include_deleted=False
                    )
                    
                    if existing_record_id:
                        logger.info(f"Found existing record (id: {existing_record_id}) after commit duplicate error. Updating instead.")
                        return await self.update(
                            db=db,
                            table_name=table_name,
                            data=normalized_data,
                            bitrix_id=str(bitrix_id_val),
                            mapping=mapping,
                            _from_insert=True
                        )
                    else:
                        # If we can't find the record, re-raise the error
                        logger.error(f"CRITICAL: Duplicate key error during commit but record not found. bitrix_id: {bitrix_id_val}")
                        raise
                else:
                    # Not a duplicate error, re-raise it
                    raise
            
            # Refresh new_record only if it exists (not None when raw SQL was used)
            if new_record:
                await db.refresh(new_record)

            logger.info(f"Successfully inserted record into {table_name} (ID: {record_id})")
            
            # STEP 2: Process documents AFTER the record is committed
            # This ensures the record exists in database before storing documents
            if table_name.lower() in ["product", "products", "supplier", "suppliers", "company", "companies", "request", "requests", "deal", "deals"]:
                try:
                    logger.info(f"📎 Processing documents for {table_name} (ID: {record_id}) AFTER record commit")
                    await self._process_documents(db, table_name, record_id, original_data_for_docs)
                except Exception as doc_error:
                    # Log error but don't fail the insert operation (record is already committed)
                    logger.error(f"❌ Error processing documents for {table_name} (ID: {record_id}): {doc_error}", exc_info=True)
                    logger.warning(f"   ⚠️ Record was successfully inserted, but document processing failed. Documents can be processed later.")

            # Serialize response
            if serializer and new_record:
                return serializer.dump(new_record)
            elif new_record:
                return {"id": new_record.id, **normalized_data}
            else:
                # When raw SQL was used, fetch the record to serialize it
                fetched_record = await db.get(model, record_id)
                if serializer and fetched_record:
                    return serializer.dump(fetched_record)
                else:
                    return {"id": record_id, **normalized_data}

        except Exception as exc:
            await db.rollback()
            logger.error(f"Error inserting record into {table_name}: {exc}", exc_info=True)
            raise

    async def update(
        self, db: AsyncSession, table_name: str, data: Dict[str, Any], bitrix_id: Optional[str] = None, mapping: Optional[List[Dict[str, Any]]] = None, _from_insert: bool = False
    ) -> Dict[str, Any]:
        """Update an existing record in the specified table."""
        try:
            logger.info(f"Updating record in {table_name}")

            model = self._get_model(table_name)
            serializer = self._get_serializer(table_name)

            # Map Bitrix field names to database column names and filter invalid fields
            mapped_data = self._map_bitrix_to_db_fields(table_name, data)
            
            # Validate and normalize data using serializer if available
            if serializer:
                try:
                    normalized_data = serializer.load(mapped_data)
                except Exception as serializer_error:
                    logger.warning(f"Serializer failed, using mapped data directly: {serializer_error}")
                    normalized_data = mapped_data.copy()
            else:
                normalized_data = mapped_data.copy()

            # Remove id from update data (should not update primary key)
            normalized_data.pop("id", None)
            
            # Map Bitrix user IDs to database user IDs for requests table
            if table_name.lower() in ["request", "requests", "deal", "deals"]:
                normalized_data = await self._map_bitrix_user_ids_to_db_ids(db, normalized_data)
            
            # Set default values for required fields
            normalized_data = BitrixWebhookMethods.set_default_values_for_required_fields(table_name, normalized_data, is_insert=False)
            
            # Normalize numeric values before filtering
            float_fields = {"freight_charges", "total", "tax_rate", "advance_payment"}
            int_fields = {
                "probability", "lead_rank", "contact_id", "estimate_id", "moved_by_id",
                "repeat_sale_segment_id", "last_activity_by", "loaded_container_quantity",
                "week_commitment", "estimated_volume", "created_by", "modified_by"
            }
            numeric_fields = float_fields | int_fields
            for field in numeric_fields:
                if field in normalized_data:
                    normalized_data[field] = self._normalize_numeric_value(normalized_data[field], field)
            
            # Normalize datetime values before filtering (handles DD.MM.YYYY format and others)
            datetime_fields = {
                "start_date", "end_date", "inquiry_date", "cargo_readiness_date", "moved_time", "last_activity_time",
                "production_date", "loading_date", "etd", "eta", "latest_date_of_shipment",
                "lc_expiry_date", "shipping_date", "next_lots_loading_dates", "last_communication_time", "last_contact"
            }
            for field in datetime_fields:
                if field in normalized_data:
                    normalized_data[field] = self._normalize_datetime_value(normalized_data[field], field)
            
            # Get actual database columns and filter out any that don't exist
            existing_columns = await self._get_existing_db_columns(db, table_name)
            
            # Get nonexistent columns (model columns that don't exist in DB)
            nonexistent_columns = await self._get_nonexistent_columns(db, table_name)
            
            # Filter out columns that don't exist in database
            normalized_data = self._filter_nonexistent_columns(
                normalized_data, existing_columns, nonexistent_columns
            )
            
            # Final safety check: remove any known nonexistent columns that might have been added back
            normalized_data = self._remove_nonexistent_columns(normalized_data, nonexistent_columns)
            
            # Regenerate deal_id for requests table if relevant fields are being updated
            if table_name.lower() in ["request", "requests", "deal", "deals"]:
                # Check if any fields that affect deal_id are being updated
                deal_id_fields = ["pi_number", "name", "company_id", "port_of_discharge", "inquiry_date"]
                if any(field in normalized_data for field in deal_id_fields):
                    try:
                        # Get the current record data to merge with update data
                        # We'll regenerate deal_id after we have the record_id
                        pass  # Will regenerate after we get the record
                    except Exception as e:
                        logger.warning(f"Could not prepare deal_id regeneration: {e}")
            
            # Extract bitrix_id from data if it contains "ID" field
            if "ID" in data and not bitrix_id:
                bitrix_id = str(data["ID"])
            
            bitrix_id_value = bitrix_id or normalized_data.get("bitrix_id")
            if not bitrix_id_value:
                raise ValueError("bitrix_id is required for update operation")
            
            # Try to find record using ORM first
            record = None
            try:
                stmt = select(model).where(model.bitrix_id == bitrix_id_value)
                result = await db.execute(stmt)
                record = result.scalar_one_or_none()
            except Exception as query_error:
                # If query fails due to missing columns (1054 = Unknown column), use raw SQL
                error_str = str(query_error)
                if "Unknown column" in error_str or "1054" in error_str:
                    logger.warning(f"Model query failed due to missing column in database, using raw SQL workaround: {error_str}")
                    # Get actual table name from model (handles singular/plural differences)
                    actual_table_name = model.__tablename__
                    
                    # Import text here to ensure it's available in exception handler scope
                    from sqlalchemy import text as sql_text
                    
                    # Use raw SQL to find and update the record
                    # First, check if record exists
                    check_stmt = sql_text(f"SELECT id FROM {actual_table_name} WHERE bitrix_id = :bitrix_id LIMIT 1")
                    check_result = await db.execute(check_stmt, {"bitrix_id": bitrix_id_value})
                    row = check_result.fetchone()
                    
                    if not row:
                        # Record not found - try to insert instead (upsert logic) ONLY if not called from insert
                        if _from_insert:
                            # If called from insert, don't try to insert again (prevent infinite loop)
                            # This should not happen if insert() correctly detected a duplicate
                            # If it does happen, it indicates a transaction isolation or timing issue
                            logger.error(f"CRITICAL: Record not found in {actual_table_name} with bitrix_id: {bitrix_id_value} but was called from insert(). This indicates a transaction isolation issue or the record was deleted between checks.")
                            raise ValueError(f"Record not found in {actual_table_name} with bitrix_id: {bitrix_id_value}. Cannot insert as this would create an infinite loop. The record should exist since insert() detected it as a duplicate.")
                        else:
                            logger.info(f"Record not found in {actual_table_name} with bitrix_id: {bitrix_id_value}, attempting insert instead")
                            try:
                                result = await self.insert(db, table_name, data, bitrix_id_value, mapping, _from_update=True)
                                logger.info(f"✅ Inserted new record in {actual_table_name} with bitrix_id: {bitrix_id_value}")
                                return result
                            except Exception as insert_error:
                                logger.error(f"Failed to insert record after update failed: {insert_error}")
                                raise ValueError(f"Record not found in {actual_table_name} with bitrix_id: {bitrix_id_value} and insert also failed: {insert_error}")
                    
                    record_id = row[0]
                    
                    # Use already filtered normalized_data (no need to filter again)
                    safe_data = normalized_data.copy()
                    
                    # Get nonexistent columns and remove them from safe_data
                    nonexistent_columns = await self._get_nonexistent_columns(db, table_name)
                    safe_data = self._remove_nonexistent_columns(safe_data, nonexistent_columns)
                    
                    if safe_data:
                        # Build UPDATE query manually
                        # Use backticks to escape column names and sanitize parameter names
                        set_clauses = []
                        update_params = {"record_id": record_id}
                        
                        # Prepare data for SQL binding - serialize JSON fields and handle None values
                        # JSON fields that cannot be null and have default=list in model
                        json_fields_with_default = {
                            "key_instructions_to_ops", "manufacturer", "hashtag", 
                            "shipping_documents", "product_category", "observer_bitrixids", "observer_ids"
                        }
                        
                        # Float fields that need explicit conversion
                        float_fields = {"freight_charges", "total", "tax_rate", "advance_payment"}
                        # Integer fields
                        int_fields = {
                            "probability", "lead_rank", "contact_id", "estimate_id", "moved_by_id",
                            "repeat_sale_segment_id", "last_activity_by", "loaded_container_quantity",
                            "week_commitment", "estimated_volume", "created_by", "modified_by"
                        }
                        numeric_fields = float_fields | int_fields
                        
                        # Datetime fields that need normalization
                        datetime_fields = {
                            "start_date", "end_date", "inquiry_date", "cargo_readiness_date", "moved_time", "last_activity_time",
                            "production_date", "loading_date", "etd", "eta", "latest_date_of_shipment",
                            "lc_expiry_date", "shipping_date", "next_lots_loading_dates", "last_communication_time", "last_contact"
                        }
                        
                        for idx, (key, value) in enumerate(safe_data.items()):
                            # Escape column name with backticks for MySQL
                            escaped_column = f"`{key}`"
                            # Use a safe parameter name (param_0, param_1, etc.) to avoid issues with special characters
                            param_name = f"param_{idx}"
                            set_clauses.append(f"{escaped_column} = :{param_name}")
                            
                            # CRITICAL: Normalize datetime fields FIRST - parse string formats like DD.MM.YYYY
                            if key in datetime_fields:
                                update_params[param_name] = self._normalize_datetime_value(value, key)
                            # CRITICAL: Normalize numeric fields - convert strings to proper types or None
                            elif key in numeric_fields:
                                update_params[param_name] = self._normalize_numeric_value(value, key)
                            # Handle JSON fields (lists, dicts) - serialize to JSON string
                            elif isinstance(value, (list, dict)):
                                try:
                                    update_params[param_name] = json.dumps(value) if value else json.dumps([])
                                except (TypeError, ValueError):
                                    # For JSON fields with default=list, use empty list instead of None
                                    update_params[param_name] = json.dumps([]) if key in json_fields_with_default else None
                            # Handle None values for JSON fields with default=list
                            elif value is None and key in json_fields_with_default:
                                update_params[param_name] = json.dumps([])
                            # Handle datetime objects - already normalized, pass as-is
                            elif isinstance(value, datetime):
                                update_params[param_name] = value
                            # Handle None values
                            elif value is None:
                                update_params[param_name] = None
                            # Handle other types as-is (but double-check for datetime/numeric fields that might have been missed)
                            else:
                                # Safety check: if this looks like it should be datetime, normalize it
                                if key in datetime_fields:
                                    update_params[param_name] = self._normalize_datetime_value(value, key)
                                # Safety check: if this looks like it should be numeric, normalize it
                                elif key in numeric_fields:
                                    update_params[param_name] = self._normalize_numeric_value(value, key)
                                else:
                                    update_params[param_name] = value
                        
                        if set_clauses:
                            update_sql = sql_text(f"UPDATE `{actual_table_name}` SET {', '.join(set_clauses)} WHERE id = :record_id")
                            await db.execute(update_sql, update_params)
                            await db.flush()  # Use flush instead of commit to allow mapping
                            
                            logger.info(f"Updated record in {actual_table_name} (ID: {record_id}) using raw SQL due to column mismatch")
                            
                            # Handle mapping data if provided (before commit)
                            if mapping:
                                await self._handle_mapping(db, table_name, mapping, record_id)
                            
                            # Regenerate deal_id for requests table if relevant fields were updated
                            await self._regenerate_and_update_deal_id(
                                db, table_name, record_id, safe_data, bitrix_id_value, actual_table_name
                            )
                            
                            # Create/update RequestStageActivity if deal_stage changed (for requests table)
                            if actual_table_name == "requests":
                                try:
                                    deal_stage = safe_data.get("deal_stage")
                                    phase = safe_data.get("phase")
                                    current_stage_id = safe_data.get("current_stage_id")
                                    
                                    if deal_stage or current_stage_id:
                                        await BitrixWebhookMethods.create_request_stage_activities(
                                            db=db,
                                            request_id=record_id,
                                            deal_stage=deal_stage,
                                            phase=phase,
                                            current_stage_id=current_stage_id
                                        )
                                except Exception as stage_error:
                                    logger.warning(f"Failed to create/update RequestStageActivity for request {record_id}: {stage_error}")
                            
                            # Process documents if this is a table that can have documents
                            if table_name.lower() in ["product", "products", "supplier", "suppliers", "company", "companies", "request", "requests", "deal", "deals"]:
                                try:
                                    # Process documents from the original data
                                    await self._process_documents(db, table_name, record_id, data)
                                except Exception as doc_error:
                                    # Log error but don't fail the update operation
                                    logger.warning(f"Error processing documents for {table_name} (ID: {record_id}): {doc_error}")
                            
                            await db.commit()
                            
                            # Return a mock result
                            return {
                                "id": record_id,
                                "bitrix_id": bitrix_id_value,
                                **safe_data
                            }
                    else:
                        logger.warning(f"No safe fields to update for {actual_table_name} (ID: {record_id})")
                        
                        # Still handle mapping even if no fields to update
                        if mapping:
                            await self._handle_mapping(db, table_name, mapping, record_id)
                            await db.commit()
                        
                        return {"id": record_id, "bitrix_id": bitrix_id_value}
                else:
                    # Re-raise if it's a different error
                    raise

            if not record:
                # Record not found - try to insert instead (upsert logic) ONLY if not called from insert
                if _from_insert:
                    # If called from insert, don't try to insert again (prevent infinite loop)
                    logger.error(f"Record not found in {table_name} with bitrix_id: {bitrix_id_value} but was called from insert(). This indicates a transaction issue.")
                    raise ValueError(f"Record not found in {table_name} with bitrix_id: {bitrix_id_value}. Cannot insert as this would create an infinite loop.")
                
                logger.info(f"Record not found in {table_name} with bitrix_id: {bitrix_id_value}, attempting insert instead")
                try:
                    result = await self.insert(db, table_name, data, bitrix_id_value, mapping, _from_update=True)
                    logger.info(f"✅ Inserted new record in {table_name} with bitrix_id: {bitrix_id_value}")
                    return result
                except Exception as insert_error:
                    logger.error(f"Failed to insert record after update failed: {insert_error}")
                    raise ValueError(f"Record not found in {table_name} with bitrix_id: {bitrix_id_value} and insert also failed: {insert_error}")

            # normalized_data is already filtered, just ensure no nonexistent columns remain
            filtered_data = self._remove_nonexistent_columns(normalized_data)

            # Update record fields with proper type normalization
            for key, value in filtered_data.items():
                if hasattr(record, key) and value is not None:
                    # Normalize numeric values before setting
                    normalized_value = self._normalize_numeric_value(value, key)
                    setattr(record, key, normalized_value)

            await db.flush()
            record_id = record.id

            # Handle mapping data if provided (before commit)
            await self._handle_mapping_safely(db, table_name, mapping, record_id)
            
            # Regenerate deal_id for requests table if relevant fields were updated
            deal_id_fields = ["pi_number", "name", "company_id", "port_of_discharge", "inquiry_date"]
            if any(field in normalized_data for field in deal_id_fields):
                # Get current record data and merge with update data
                current_data = {key: getattr(record, key, None) for key in deal_id_fields if hasattr(record, key)}
                current_data.update({k: v for k, v in normalized_data.items() if k in deal_id_fields})
                # Regenerate and update deal_id
                await self._regenerate_and_update_deal_id(
                    db, table_name, record_id, current_data, bitrix_id_value
                )
                # Also update the record object for consistency
                if hasattr(record, 'deal_id'):
                    # Fetch the updated deal_id from database
                    from sqlalchemy import text
                    result = await db.execute(
                        text("SELECT deal_id FROM requests WHERE id = :request_id LIMIT 1"),
                        {"request_id": record_id}
                    )
                    row = result.fetchone()
                    if row and row[0]:
                        record.deal_id = row[0]
            
            # Process documents if this is a table that can have documents
            if table_name.lower() in ["product", "products", "supplier", "suppliers", "company", "companies", "request", "requests", "deal", "deals"]:
                try:
                    # Process documents from the original data (before mapping)
                    await self._process_documents(db, table_name, record_id, data)
                except Exception as doc_error:
                    # Log error but don't fail the update operation
                    logger.warning(f"Error processing documents for {table_name} (ID: {record_id}): {doc_error}")

            # Create/update RequestStageActivity if deal_stage changed
            if table_name.lower() in ["request", "requests", "deal", "deals"]:
                try:
                    deal_stage = normalized_data.get("deal_stage") or (record.deal_stage if hasattr(record, 'deal_stage') else None)
                    phase = normalized_data.get("phase") or (record.phase.value if hasattr(record, 'phase') and record.phase else None)
                    current_stage_id = normalized_data.get("current_stage_id") or (record.current_stage_id if hasattr(record, 'current_stage_id') else None)
                    
                    if deal_stage or current_stage_id:
                        await BitrixWebhookMethods.create_request_stage_activities(
                            db=db,
                            request_id=record_id,
                            deal_stage=deal_stage,
                            phase=phase,
                            current_stage_id=current_stage_id
                        )
                except Exception as stage_error:
                    # Log error but don't fail the update operation
                    logger.warning(f"Failed to create/update RequestStageActivity for request {record_id}: {stage_error}")

            # Commit all changes (product update + mappings) together
            await db.commit()
            await db.refresh(record)

            logger.info(f"Successfully updated record in {table_name} (ID: {record_id})")

            # Serialize response
            if serializer:
                return serializer.dump(record)
            else:
                return {"id": record.id, **normalized_data}

        except Exception as exc:
            await db.rollback()
            logger.error(f"Error updating record in {table_name}: {exc}", exc_info=True)
            raise

    async def delete_record(
        self, db: AsyncSession, table_name: str, bitrix_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a record from the specified table (always performs soft delete)."""
        # Always perform soft delete - set delete_type at the beginning
        delete_type = "soft"
        
        try:
            logger.info(f"Deleting record from {table_name} (soft delete)")

            # Find record by bitrix_id
            if not bitrix_id:
                raise ValueError("bitrix_id is required for delete operation")

            # Map table name to actual database table name
            table_lower = table_name.lower()
            actual_table_name = None
            
            # Handle company/supplier/customer mapping
            if table_lower in ["company", "companies", "supplier", "suppliers"]:
                actual_table_name = "suppliers"
            elif table_lower in ["customer", "customers", "contact", "contacts"]:
                actual_table_name = "customers"
            elif table_lower in ["deal", "deals", "request", "requests"]:
                actual_table_name = "requests"
            else:
                # Get actual table name from model
                try:
                    model = self._get_model(table_name)
                    actual_table_name = model.__tablename__
                except Exception:
                    # Fallback to table_name if model not found
                    actual_table_name = table_name.lower()
            
            # First, try to find in suppliers table
            record_id = None
            found_table = None
            
            if actual_table_name == "suppliers" or table_lower in ["company", "companies", "supplier", "suppliers"]:
                # Check suppliers table
                # Handle zero dates - MySQL doesn't accept '0000-00-00 00:00:00' in direct comparisons
                result = await db.execute(
                    text("SELECT id FROM suppliers WHERE bitrix_id = :bitrix_id AND (deleted_at IS NULL OR YEAR(deleted_at) = 0) LIMIT 1"),
                    {"bitrix_id": bitrix_id}
                )
                row = result.fetchone()
                if row:
                    record_id = row[0]
                    found_table = "suppliers"
                    actual_table_name = "suppliers"
            
            # If not found in suppliers, check customers table (for company delete events)
            if not record_id and table_lower in ["company", "companies"]:
                # Handle zero dates - MySQL doesn't accept '0000-00-00 00:00:00' in direct comparisons
                result = await db.execute(
                    text("SELECT id FROM customers WHERE bitrix_id = :bitrix_id AND (deleted_at IS NULL OR YEAR(deleted_at) = 0) LIMIT 1"),
                    {"bitrix_id": bitrix_id}
                )
                row = result.fetchone()
                if row:
                    record_id = row[0]
                    found_table = "customers"
                    actual_table_name = "customers"
            
            # If not found, check requests table (for deal/request delete events)
            if not record_id and actual_table_name == "requests":
                # Handle zero dates - MySQL doesn't accept '0000-00-00 00:00:00' in direct comparisons
                result = await db.execute(
                    text("SELECT id FROM requests WHERE bitrix_id = :bitrix_id AND (deleted_at IS NULL OR YEAR(deleted_at) = 0) LIMIT 1"),
                    {"bitrix_id": bitrix_id}
                )
                row = result.fetchone()
                if row:
                    record_id = row[0]
                    found_table = "requests"
                    actual_table_name = "requests"
            
            # If still not found, try the mapped table
            if not record_id:
                # Handle zero dates - MySQL doesn't accept '0000-00-00 00:00:00' in direct comparisons
                result = await db.execute(
                    text(f"SELECT id FROM `{actual_table_name}` WHERE bitrix_id = :bitrix_id AND (deleted_at IS NULL OR YEAR(deleted_at) = 0) LIMIT 1"),
                    {"bitrix_id": bitrix_id}
                )
                row = result.fetchone()
                if row:
                    record_id = row[0]
                    found_table = actual_table_name

            if not record_id:
                # Record not found - might already be deleted or never existed
                # Return success response (idempotent delete operation)
                logger.warning(f"Record not found in {actual_table_name} with bitrix_id: {bitrix_id} - may already be deleted")
                return {
                    "bitrix_id": bitrix_id,
                    "delete_type": "not_found",
                    "success": True,
                    "message": f"Record with bitrix_id {bitrix_id} not found in {actual_table_name} (may already be deleted)",
                }

            # Delete related mappings before soft deleting the record
            deleted_mappings = []
            
            try:
                if actual_table_name == "requests":
                    count = await BitrixWebhookMethods.delete_request_products_mappings(db, record_id)
                    deleted_mappings.append(f"request_products: {count} records")
                    count = await BitrixWebhookMethods.delete_request_customers_mappings(db, record_id)
                    deleted_mappings.append(f"request_customers: {count} records")
                elif actual_table_name == "suppliers":
                    count = await BitrixWebhookMethods.delete_product_suppliers_mappings_by_supplier(db, record_id)
                    deleted_mappings.append(f"product_suppliers: {count} records")
                    count = await BitrixWebhookMethods.update_requests_company_id_to_null(db, record_id)
                    deleted_mappings.append(f"requests.company_id: {count} records updated")
                elif actual_table_name == "customers":
                    count = await BitrixWebhookMethods.delete_request_customers_mappings_by_customer(db, record_id)
                    deleted_mappings.append(f"request_customers: {count} records")
                elif actual_table_name == "products":
                    count = await BitrixWebhookMethods.delete_request_products_mappings_by_product(db, record_id)
                    deleted_mappings.append(f"request_products: {count} records")
                    count = await BitrixWebhookMethods.delete_product_suppliers_mappings_by_product(db, record_id)
                    deleted_mappings.append(f"product_suppliers: {count} records")
            except Exception as e:
                logger.warning(f"Error deleting related mappings: {e}")
            
            # Perform soft delete
            rows_affected = await BitrixWebhookMethods.soft_delete_record(db, actual_table_name, record_id)
            
            if rows_affected == 0:
                logger.warning(f"No rows updated for soft delete in {actual_table_name} (ID: {record_id}, bitrix_id: {bitrix_id})")
            else:
                logger.info(f"Soft deleted record from {actual_table_name} (ID: {record_id}, bitrix_id: {bitrix_id})")
            
            # Verify the delete was successful
            deleted_at = await BitrixWebhookMethods.verify_deleted_at(db, actual_table_name, record_id)
            if deleted_at:
                logger.info(f"✅ Verified: deleted_at is set to {deleted_at} for {actual_table_name} (ID: {record_id})")
            else:
                logger.warning(f"⚠️ Warning: deleted_at is still NULL for {actual_table_name} (ID: {record_id})")
            
            await db.commit()
            
            if deleted_mappings:
                logger.info(f"Deleted related mappings: {', '.join(deleted_mappings)}")

            return {
                "id": record_id,
                "bitrix_id": bitrix_id,
                "delete_type": delete_type,
                "success": True,
                "table": found_table or actual_table_name,
                "deleted_mappings": deleted_mappings,
            }

        except Exception as exc:
            await db.rollback()
            logger.error(f"Error deleting record from {table_name}: {exc}", exc_info=True)
            raise

    def _build_bitrix_cookies(self) -> Dict[str, str]:
        """Build Bitrix cookies dictionary from environment variables."""
        cookie_vars = ["USER_LANG", "BITRIX_SM_UIDL", "BITRIX_SM_SALE_UID", "BITRIX_SM_TZ",
                      "BITRIX_SM_PK", "BITRIX_SM_UIDH", "BITRIX_SM_CC", "BITRIX_SM_kernel",
                      "BITRIX_SM_DTOKEN", "BITRIX_SM_SOUND_LOGIN_PLAYED", "qmb",
                      "BITRIX_SM_kernel_0", "PHPSESSID"]
        return {var: getattr(settings, var) for var in cookie_vars if getattr(settings, var, None)}

    async def _get_doc_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session for document downloads."""
        if self._doc_session is None or self._doc_session.closed:
            self._doc_session = aiohttp.ClientSession()
        return self._doc_session

    def _get_doc_table_type(self, table_name: str) -> str:
        """Get table type for document field lookup."""
        table_lower = table_name.lower()
        if table_lower in ["product", "products"]:
            return "product"
        elif table_lower in ["supplier", "suppliers", "company", "companies"]:
            return "supplier"
        elif table_lower in ["request", "requests", "deal", "deals"]:
            return "request"
        return ""

    def _extract_documents(self, data: Dict[str, Any], table_type: str) -> List[Tuple[str, Dict[str, str]]]:
        """Extract all documents from data in one pass."""
        documents = []
        fields_to_check = set(self.DOCUMENT_FIELDS_MAP.get(table_type, []))
        logger.info(f"🔍 Document fields to check for {table_type}: {fields_to_check}")
        logger.info(f"🔍 Data keys available (first 30): {list(data.keys())[:30]}")
        
        for field_name, field_value in data.items():
            if not field_value:
                continue
            
            # Normalize field name for comparison
            normalized_field = self._normalize_field_name(field_name)
            
            # Check if field is in document fields map or contains document URLs
            is_document_field = normalized_field in fields_to_check
            has_document_value = self._is_document_value(field_value)
            
            if is_document_field:
                logger.info(f"✅ Found document field (in map): '{field_name}' (normalized: '{normalized_field}')")
            elif has_document_value:
                logger.info(f"✅ Found document field (has URLs): '{field_name}' (normalized: '{normalized_field}')")
            
            if is_document_field or has_document_value:
                logger.info(f"   Field value type: {type(field_value)}, Value preview: {str(field_value)[:200]}")
                docs = self._parse_document_value(field_value)
                logger.info(f"   Parsed {len(docs)} document(s) from field '{field_name}'")
                if docs:
                    for i, doc in enumerate(docs):
                        doc_name = f"{field_name}_{i}" if i > 0 else field_name
                        documents.append((doc_name, doc))
                        logger.info(f"   📎 Document {i+1}: showUrl={doc.get('showUrl', 'N/A')[:100]}, downloadUrl={doc.get('downloadUrl', 'N/A')[:100]}")
        
        logger.info(f"📦 Total documents extracted: {len(documents)}")
        return documents

    def _is_document_value(self, value: Any) -> bool:
        """Check if value contains document URLs."""
        if isinstance(value, dict):
            return "showUrl" in value or "downloadUrl" in value
        if isinstance(value, list):
            return any(isinstance(item, dict) and ("showUrl" in item or "downloadUrl" in item) 
                      for item in value)
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return "showUrl" in parsed or "downloadUrl" in parsed
                if isinstance(parsed, list):
                    return any(isinstance(item, dict) and ("showUrl" in item or "downloadUrl" in item) 
                              for item in parsed)
            except (json.JSONDecodeError, TypeError):
                # Check for showUrl or downloadUrl in string (handles both single and double quotes)
                return bool(re.search(r'["\']showUrl["\']|["\']downloadUrl["\']', value, re.IGNORECASE))
        return False

    def _parse_document_value(self, value: Any) -> List[Dict[str, str]]:
        """Parse document value into list of document dicts. Handles JSON, string dicts, and Python dicts."""
        if isinstance(value, str):
            # Try JSON first
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Try parsing Python dict string (with single quotes)
                # Example: "{'showUrl': '/path', 'downloadUrl': '/path'}"
                try:
                    # Replace single quotes with double quotes for JSON parsing
                    json_str = value.replace("'", '"')
                    value = json.loads(json_str)
                except (json.JSONDecodeError, TypeError):
                    # Try regex extraction for showUrl/downloadUrl
                    show_match = re.search(r'["\']showUrl["\']\s*:\s*["\']((?:[^"\'\\]|\\.)*)["\']', value)
                    download_match = re.search(r'["\']downloadUrl["\']\s*:\s*["\']((?:[^"\'\\]|\\.)*)["\']', value)
                    if show_match or download_match:
                        doc = {}
                        if show_match:
                            url = show_match.group(1)
                            doc["showUrl"] = url if url.startswith("http") else f"https://dana.bitrix24.eu{url}"
                        if download_match:
                            url = download_match.group(1)
                            doc["downloadUrl"] = url if url.startswith("http") else f"https://dana.bitrix24.eu{url}"
                        return [doc] if doc else []
                    return []
        
        # Handle dict
        if isinstance(value, dict):
            # Check if it's a document dict
            if "showUrl" in value or "downloadUrl" in value:
                # Ensure URLs are complete
                doc = {}
                if "showUrl" in value:
                    url = str(value["showUrl"])
                    doc["showUrl"] = url if url.startswith("http") else f"https://dana.bitrix24.eu{url}"
                if "downloadUrl" in value:
                    url = str(value["downloadUrl"])
                    doc["downloadUrl"] = url if url.startswith("http") else f"https://dana.bitrix24.eu{url}"
                return [doc] if doc else []
            # If dict doesn't have showUrl/downloadUrl, return empty
            return []
        
        # Handle list
        if isinstance(value, list):
            docs = []
            for item in value:
                if isinstance(item, dict) and ("showUrl" in item or "downloadUrl" in item):
                    doc = {}
                    if "showUrl" in item:
                        url = str(item["showUrl"])
                        doc["showUrl"] = url if url.startswith("http") else f"https://dana.bitrix24.eu{url}"
                    if "downloadUrl" in item:
                        url = str(item["downloadUrl"])
                        doc["downloadUrl"] = url if url.startswith("http") else f"https://dana.bitrix24.eu{url}"
                    if doc:
                        docs.append(doc)
            return docs
        
        return []

    async def _download_file_with_oauth(self, download_url: str, session: aiohttp.ClientSession) -> Optional[Tuple[bytes, str]]:
        """
        Download file using webhook token in URL auth parameter.
        
        Args:
            download_url: URL to download from
            session: aiohttp session
            
        Returns:
            Tuple of (file_content, content_type) or None if failed
        """
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        # Get webhook token from BITRIX_WEBHOOK_URL
        bitrix_webhook_url = getattr(settings, "BITRIX_WEBHOOK_URL", None)
        if not bitrix_webhook_url:
            # Try to get from BITRIX_URL or use default
            bitrix_webhook_url = getattr(settings, "BITRIX_URL", None) or "https://dana.bitrix24.eu/rest/218/8cxeo979k998jzqq/"
        
        # Extract webhook token from URL
        # URL format: https://domain.bitrix24.eu/rest/USER_ID/WEBHOOK_TOKEN/ or https://domain.bitrix24.eu/rest/USER_ID/WEBHOOK_TOKEN
        webhook_token = None
        if bitrix_webhook_url:
            # Remove trailing slash if present
            bitrix_webhook_url_clean = bitrix_webhook_url.rstrip("/")
            # Extract token (last part after /)
            parts = bitrix_webhook_url_clean.split("/")
            if len(parts) > 0:
                webhook_token = parts[-1]
                # Validate token is not empty and looks like a token (alphanumeric, at least 10 chars)
                if webhook_token and len(webhook_token) >= 10:
                    logger.debug(f"Extracted webhook token from URL: {webhook_token[:10]}... (length: {len(webhook_token)})")
                else:
                    logger.warning(f"⚠️ Extracted token seems invalid (too short or empty): {webhook_token}")
                    webhook_token = None
        
        if not webhook_token:
            logger.error(f"❌ Could not extract valid webhook token from BITRIX_WEBHOOK_URL: {bitrix_webhook_url}")
            logger.error(f"   Expected format: https://domain.bitrix24.eu/rest/USER_ID/WEBHOOK_TOKEN")
            logger.error(f"   Current value: {bitrix_webhook_url}")
        
        # Use webhook token in URL auth parameter
        if webhook_token:
            try:
                # Parse URL and add/update auth parameter
                parsed = urlparse(download_url)
                query_params = parse_qs(parsed.query)
                
                # Update or add auth parameter with webhook token
                query_params["auth"] = [webhook_token]
                
                # Reconstruct URL
                new_query = urlencode(query_params, doseq=True)
                new_parsed = parsed._replace(query=new_query)
                authenticated_url = urlunparse(new_parsed)
                
                logger.info(f"🔐 Trying download with webhook token in URL auth parameter")
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "*/*",
                }
                
                # Retry logic for webhook token download
                for attempt in range(3):
                    try:
                        async with session.get(
                            authenticated_url,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=60),
                            allow_redirects=True
                        ) as response:
                            status = response.status
                            content_type = response.headers.get("Content-Type", "unknown")
                            
                            logger.debug(f"Webhook token download attempt {attempt + 1}: Status {status}, Content-Type: {content_type}")
                            
                            if status == 200:
                                content = await response.read()
                                
                                # Safety check: Block HTML responses
                                if "text/html" in content_type.lower() or content.startswith(b"<!DOCTYPE") or content.startswith(b"<html"):
                                    logger.warning(f"⚠️ Bitrix returned HTML with webhook token method - attempt {attempt + 1}")
                                    if attempt < 2:
                                        await asyncio.sleep(2 ** attempt)
                                        continue
                                else:
                                    logger.info(f"✅ Successfully downloaded {len(content)} bytes using webhook token in URL")
                                    return content, content_type
                            else:
                                logger.warning(f"Non-200 status: {status} - attempt {attempt + 1}")
                                if attempt < 2:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                    except Exception as e:
                        logger.warning(f"Download error with webhook token (attempt {attempt + 1}): {e}")
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)
                            continue
            except Exception as e:
                logger.warning(f"Download error with webhook token: {e}")
        
        # If webhook token is not available
        if not webhook_token:
            logger.error(f"❌ No webhook token available. Cannot download file.")
            logger.error(f"   🔧 SOLUTION: Configure BITRIX_WEBHOOK_URL in your .env file:")
            logger.error(f"      BITRIX_WEBHOOK_URL=your_webhook_url (will extract token)")
            logger.error(f"   Without webhook token, Bitrix file downloads will fail (returns HTML login page).")
        else:
            logger.error(f"❌ Download failed with webhook token method. File download unsuccessful.")
        
        return None

    async def _download_document_file(self, download_url: str) -> Optional[Tuple[bytes, str]]:
        """
        Download file from Bitrix using REST API (RECOMMENDED METHOD - Option 1).
        
        Step 1: Call crm.product.get to get file info with DOWNLOAD_URL
        Step 2: Download using the authenticated URL from REST API
        
        This is more secure and stable than direct download.php URLs.
        """
        from urllib.parse import urlparse, parse_qs
        import aiohttp
        
        # Extract parameters from URL
        parsed = urlparse(download_url)
        query_params = parse_qs(parsed.query)
        file_id = query_params.get("fileId", [None])[0]
        product_id = query_params.get("productId", [None])[0]
        field_name = query_params.get("fieldName", [None])[0]
        
        if not file_id:
            logger.error(f"Could not extract fileId from URL: {download_url}")
            return None
        
        # Bitrix REST API webhook URL
        bitrix_webhook_url = getattr(settings, "BITRIX_WEBHOOK_URL", None) or "https://dana.bitrix24.eu/rest/218/8cxeo979k998jzqq/"
        session = await self._get_doc_session()
        
        # OPTION 1 (BEST): Use Bitrix REST API to get authenticated download URL
        # Step 1: Get file info from crm.product.get
        if product_id and field_name:
            try:
                logger.info(f"🔐 Step 1: Getting file info from Bitrix REST API (crm.product.get)")
                logger.debug(f"   Product ID: {product_id}, Field: {field_name}, File ID: {file_id}")
                
                api_url = f"{bitrix_webhook_url}crm.product.get"
                params = {"id": product_id}
                
                async with session.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as api_response:
                    if api_response.status == 200:
                        api_data = await api_response.json()
                        
                        # Check for API errors
                        if "error" in api_data:
                            error_desc = api_data.get("error_description", "Unknown error")
                            logger.error(f"❌ Bitrix API error: {error_desc}")
                        else:
                            # Get product data
                            product_data = api_data.get("result", {})
                            
                            # Get the property field - try multiple strategies
                            field_data = None
                            authenticated_download_url = None
                            
                            # Strategy 1: Try exact field name match
                            if field_name in product_data:
                                field_value = product_data[field_name]
                                logger.debug(f"Found field '{field_name}' via exact match")
                                
                                # Handle different field value structures
                                if isinstance(field_value, dict):
                                    # Single file object
                                    field_data = field_value
                                elif isinstance(field_value, list):
                                    # Multiple files - find the one matching file_id
                                    logger.debug(f"Field '{field_name}' is a list with {len(field_value)} items, searching for file ID {file_id}")
                                    for item in field_value:
                                        if isinstance(item, dict):
                                            # Check if this item matches the file_id
                                            # Item might be {'valueId': ..., 'value': {'id': ...}} or {'id': ...}
                                            item_id = None
                                            if "value" in item and isinstance(item["value"], dict):
                                                item_id = str(item["value"].get("id", ""))
                                            else:
                                                item_id = str(item.get("ID", "") or item.get("id", ""))
                                            
                                            if item_id == str(file_id) or file_id in str(item):
                                                field_data = item
                                                logger.debug(f"Found matching file in list: ID {item_id}")
                                                break
                                    # If no match found, use first item as fallback
                                    if not field_data and field_value:
                                        field_data = field_value[0]
                                        logger.debug(f"Using first item from list as fallback")
                                elif field_value is None:
                                    logger.warning(f"Field '{field_name}' exists but is None")
                                else:
                                    logger.debug(f"Field '{field_name}' has unexpected type: {type(field_value)}")
                            
                            # Strategy 2: Search for field containing the file ID (if Strategy 1 didn't work)
                            if (not field_data or not isinstance(field_data, dict)) and file_id:
                                logger.debug(f"Field '{field_name}' not found or invalid, searching for field with file ID {file_id}")
                                for key, value in product_data.items():
                                    if isinstance(value, dict):
                                        # Check if this dict contains the file ID
                                        item_id = str(value.get("ID", ""))
                                        if item_id == str(file_id) or file_id in str(value):
                                            field_data = value
                                            logger.debug(f"Found field '{key}' containing file ID {file_id}")
                                            break
                                    elif isinstance(value, list):
                                        # Check list items
                                        for item in value:
                                            if isinstance(item, dict):
                                                item_id = str(item.get("ID", ""))
                                                if item_id == str(file_id) or file_id in str(item):
                                                    field_data = item
                                                    logger.debug(f"Found file ID {file_id} in list field '{key}'")
                                                    break
                                        if field_data:
                                            break
                            
                            # Strategy 3: Search for PROPERTY_* fields that might contain files
                            if not field_data or not isinstance(field_data, dict):
                                logger.debug(f"Searching for PROPERTY_* fields with download URLs")
                                for key, value in product_data.items():
                                    if key.startswith("PROPERTY_") or "PROPERTY" in key.upper():
                                        if isinstance(value, dict):
                                            if "DOWNLOAD_URL" in value or "downloadUrl" in value:
                                                field_data = value
                                                logger.debug(f"Found property field '{key}' with download URL")
                                                break
                                        elif isinstance(value, list) and value:
                                            # Check first item in list
                                            first_item = value[0] if isinstance(value[0], dict) else None
                                            if first_item and ("DOWNLOAD_URL" in first_item or "downloadUrl" in first_item):
                                                field_data = first_item
                                                logger.debug(f"Found property field '{key}' with download URL in list")
                                                break
                            
                            # Extract download URL from field_data
                            if field_data and isinstance(field_data, dict):
                                # Get DOWNLOAD_URL from the field data
                                # Handle nested structure: field_data may have {'valueId': ..., 'value': {'downloadUrl': ...}}
                                authenticated_download_url = None
                                
                                # Check direct keys first
                                authenticated_download_url = field_data.get("DOWNLOAD_URL") or field_data.get("downloadUrl")
                                
                                # If not found, check nested 'value' structure
                                if not authenticated_download_url and "value" in field_data:
                                    value_dict = field_data.get("value")
                                    if isinstance(value_dict, dict):
                                        authenticated_download_url = value_dict.get("DOWNLOAD_URL") or value_dict.get("downloadUrl")
                                        logger.debug(f"Found downloadUrl in nested 'value' structure")
                                
                                # If still not found, check if field_data itself is the value
                                if not authenticated_download_url:
                                    # Check if field_data has 'id' and 'downloadUrl' directly (it might be the file object)
                                    if "id" in field_data and ("downloadUrl" in field_data or "DOWNLOAD_URL" in field_data):
                                        authenticated_download_url = field_data.get("DOWNLOAD_URL") or field_data.get("downloadUrl")
                                
                                if authenticated_download_url:
                                    logger.info(f"✅ Got authenticated download URL from Bitrix REST API")
                                    return await self._download_file_with_oauth(authenticated_download_url, session)
                                else:
                                    logger.warning(f"⚠️ Field does not contain DOWNLOAD_URL")
                                    logger.debug(f"   Field data keys: {list(field_data.keys())}")
                                    logger.debug(f"   Field data sample: {str(field_data)[:200]}")
                            else:
                                logger.warning(f"⚠️ Field '{field_name}' not found or invalid in product data")
                                logger.debug(f"   Available fields: {list(product_data.keys())[:30]}")
                                # Log the actual field value if it exists
                                if field_name in product_data:
                                    field_value = product_data[field_name]
                                    logger.debug(f"   Field '{field_name}' value type: {type(field_value)}, value: {str(field_value)[:200]}")
                    else:
                        logger.warning(f"⚠️ Bitrix API returned status {api_response.status}")
                        
            except Exception as e:
                logger.error(f"❌ Error calling Bitrix REST API: {e}", exc_info=True)
        
        # OPTION 2: Try using Bitrix REST API download method (if we have file_id)
        if file_id and product_id:
            try:
                logger.info(f"🔐 Attempting Bitrix REST API download method")
                # Use Bitrix REST API download endpoint
                download_api_url = f"{bitrix_webhook_url}download"
                params = {
                    "id": file_id,
                    "ownerTypeId": 5,  # 5 = Product in Bitrix
                    "ownerId": product_id
                }
                
                async with session.get(download_api_url, params=params, timeout=aiohttp.ClientTimeout(total=60)) as api_response:
                    if api_response.status == 200:
                        content_type = api_response.headers.get("Content-Type", "application/octet-stream")
                        content = await api_response.read()
                        
                        # Check if we got HTML (authentication failure)
                        if "text/html" in content_type.lower() or content.startswith(b"<!DOCTYPE") or content.startswith(b"<html"):
                            logger.warning(f"⚠️ Bitrix REST API download returned HTML (may need authentication)")
                        else:
                            logger.info(f"✅ Successfully downloaded {len(content)} bytes via Bitrix REST API")
                            return content, content_type
                    else:
                        logger.warning(f"⚠️ Bitrix REST API download returned status {api_response.status}")
            except Exception as e:
                logger.warning(f"⚠️ Bitrix REST API download failed: {e}")
        
        # OPTION 3: Fallback - Try direct download with webhook token in URL
        logger.info(f"⚠️ Falling back to direct download method with webhook token in URL")
        
        if not download_url.startswith("http"):
            download_url = f"https://dana.bitrix24.eu{download_url}"
        
        # Extract webhook token from bitrix_webhook_url for direct URL modification
        webhook_token_for_url = None
        if bitrix_webhook_url:
            bitrix_webhook_url_clean = bitrix_webhook_url.rstrip("/")
            parts = bitrix_webhook_url_clean.split("/")
            if len(parts) > 0:
                webhook_token_for_url = parts[-1]
        
        # Try to add auth parameter to the download URL if it's missing or empty
        if "auth=" in download_url:
            auth_value = download_url.split("auth=")[1].split("&")[0]
            if not auth_value and webhook_token_for_url:
                download_url = download_url.replace("auth=", f"auth={webhook_token_for_url}")
                logger.debug(f"Added webhook token to download URL auth parameter")
        elif webhook_token_for_url:
            # No auth parameter at all, add it
            separator = "&" if "?" in download_url else "?"
            download_url = f"{download_url}{separator}auth={webhook_token_for_url}"
            logger.debug(f"Added webhook token as new auth parameter to download URL")
        
        return await self._download_file_with_oauth(download_url, session)

    def _detect_file_type(self, file_content: bytes, url: Optional[str] = None) -> Tuple[str, str]:
        """Detect file type and extension."""
        magic_map = {
            b"\x89PNG\r\n\x1a\n": ("image/png", ".png"),
            b"\xff\xd8\xff": ("image/jpeg", ".jpg"),
            b"GIF87a": ("image/gif", ".gif"),
            b"GIF89a": ("image/gif", ".gif"),
            b"%PDF": ("application/pdf", ".pdf"),
            b"PK\x03\x04": ("application/zip", ".zip"),
            b"\x50\x4b\x03\x04": ("application/zip", ".zip"),
        }
        
        for magic, (mime, ext) in magic_map.items():
            if file_content.startswith(magic):
                return mime, ext
        
        if file_content.startswith(b"<?xml") or file_content.startswith(b"<"):
            if b"<!DOCTYPE html" in file_content[:1024] or b"<html" in file_content[:1024]:
                return "text/html", ".html"
            return "application/xml", ".xml"
        
        if url:
            parsed = urlparse(url)
            if "." in parsed.path:
                ext = "." + parsed.path.split(".")[-1].lower()
                mime = mimetypes.guess_type(parsed.path)[0] or "application/octet-stream"
                return mime, ext
        
        return "application/octet-stream", ".bin"

    def _generate_blob_path(self, table_type: str, record_id: int, field_name: str, 
                           file_id: str, extension: str) -> str:
        """Generate Azure Blob Storage path."""
        clean_field = re.sub(r"[^a-zA-Z0-9_]", "_", field_name).lower()
        filename = f"document_{file_id}{extension}"
        
        path_map = {
            "product": f"uploads/documents/products/{record_id}/{clean_field}/{filename}",
            "supplier": f"documents/supplier/{record_id}/{filename}",
            "request": f"documents/requests/{record_id}/{clean_field}/{filename}",
        }
        return path_map.get(table_type, f"documents/{table_type}/{record_id}/{filename}")

    def _normalize_source_table(self, table_name: str) -> str:
        """Normalize table name to source_table format."""
        if not table_name:
            logger.warning(f"⚠️ _normalize_source_table received empty table_name, defaulting to 'requests'")
            return "requests"
        
        table_lower = table_name.lower().rstrip("s")
        if table_lower == "companie":
            return "suppliers"
        if table_lower == "deal":
            return "requests"
        
        # Check if it matches known table types (return plural forms to match actual table names)
        if table_lower == "product":
            return "products"
        elif table_lower == "supplier":
            return "suppliers"
        elif table_lower == "request":
            return "requests"
        
        # Fallback: try to match common table name patterns
        if "product" in table_lower:
            return "products"
        elif "supplier" in table_lower or "companie" in table_lower:
            return "suppliers"
        elif "deal" in table_lower or "request" in table_lower:
            return "requests"
        
        # Last resort: return the original table name (lowercased)
        logger.warning(f"⚠️ Could not normalize table_name '{table_name}' to known source_table, using '{table_name.lower()}'")
        return table_name.lower()

    async def _check_documents_exist(self, db: AsyncSession, blob_paths: List[str], 
                                     record_id: int, source_table: str) -> Dict[str, bool]:
        """Batch check if documents exist by checking paths against database."""
        if not blob_paths:
            return {}
        
        try:
            # blob_paths should already be actual paths (not JSON)
            if not blob_paths:
                return {path: False for path in blob_paths}
            
            # Check if documents exist with these paths
            placeholders = ", ".join([f":path_{i}" for i in range(len(blob_paths))])
            params = {"mapping_id": record_id, "source_table": source_table}
            params.update({f"path_{i}": path for i, path in enumerate(blob_paths)})
            
            result = await db.execute(
                text(f"""
                    SELECT path FROM documents 
                    WHERE path IN ({placeholders}) AND mapping_id = :mapping_id AND source_table = :source_table
                """),
                params,
            )
            existing_paths = {row[0] for row in result.fetchall()}
            
            # Return map of path -> exists
            return {path: path in existing_paths for path in blob_paths}
        except Exception as e:
            logger.error(f"Error checking documents: {e}", exc_info=True)
            return {path: False for path in blob_paths}

    async def _process_single_document(
        self, db: AsyncSession, table_type: str, record_id: int, source_table: str,
        field_name: str, url_data: Dict[str, str], blob_path: str
    ) -> Optional[Dict[str, Any]]:
        """Process a single document: download from Bitrix, upload to Azure, return document metadata.
        
        IMPORTANT: Always returns metadata to store in database, even if download/upload fails.
        If download fails, stores original Bitrix URL as path.
        If download succeeds but upload fails, stores Bitrix URL as path.
        If both succeed, stores Azure blob URL as path.
        """
        # Validate source_table is provided
        if not source_table or source_table.strip() == "":
            logger.error(f"❌ source_table is required but was not provided for document processing")
            logger.error(f"   table_type: {table_type}, record_id: {record_id}, field_name: {field_name}")
            logger.error(f"   Attempting to normalize from table_type: '{table_type}'")
            # Try to normalize from table_type as fallback
            source_table = self._normalize_source_table(table_type) if table_type else "requests"
            logger.warning(f"   ⚠️ Using fallback source_table: '{source_table}'")
            if not source_table or source_table.strip() == "":
                logger.error(f"   ❌ Fallback also failed, cannot process document")
                return None
        
        download_url = url_data.get("downloadUrl") or url_data.get("showUrl")
        if not download_url:
            logger.warning(f"No download URL found in url_data: {url_data}")
            return None
        
        logger.info(f"📋 Processing document for source_table: '{source_table}' (table that this document belongs to), mapping_id: {record_id}")
        
        # Ensure download_url is complete
        if not download_url.startswith("http"):
            download_url = f"https://dana.bitrix24.eu{download_url}"
        
        parsed = urlparse(download_url)
        file_id = parse_qs(parsed.query).get("fileId", ["unknown"])[0]
        
        # Initialize default values (will be used if download fails)
        file_type = "application/octet-stream"
        extension = ""
        file_size = 0
        full_path = download_url  # Default to Bitrix URL if download fails
        
        # Try to extract file extension from URL
        if "." in parsed.path:
            extension = "." + parsed.path.split(".")[-1].lower()
        
        # Step 1: Try to download file from Bitrix
        logger.info(f"📥 Step 1: Attempting to download document from Bitrix")
        logger.debug(f"   Download URL before processing: {download_url}")
        result = await self._download_document_file(download_url)
        
        if not result:
            logger.warning(f"⚠️ Step 1 FAILED: Could not download document from {download_url}.")
            logger.info(f"   💡 Storing document with original Bitrix URL in database.")
            logger.info(f"   🔧 TROUBLESHOOTING: Check if BITRIX_WEBHOOK_URL is configured in .env file")
            
            # Return metadata when download failed
            # path: Store Bitrix URL data as JSON string (showUrl and downloadUrl dict)
            # url: Store blob storage URL (even if upload will fail, we store the intended blob URL)
            # Build blob URL (even if file wasn't uploaded, we store the intended URL)
            azure_blob_storage_url = getattr(settings, "AZURE_BLOB_STORAGE_URL", None)
            if azure_blob_storage_url:
                azure_blob_storage_url = azure_blob_storage_url.rstrip("/")
                blob_url = f"{azure_blob_storage_url}/{blob_path}"
            else:
                blob_url = blob_path
            
            # Convert url_data dict to JSON string for path field
            path_json = json.dumps(url_data) if isinstance(url_data, dict) else str(url_data)
            
            logger.info(f"   📋 Document metadata: source_table='{source_table}' (belongs to {source_table} table), mapping_id={record_id}")
            return {
                "path": path_json,  # Store Bitrix URL data as JSON string: "{'showUrl': '...', 'downloadUrl': '...'}"
                "url": blob_url,  # Store blob storage URL (Azure blob URL)
                "file_name": f"document_{file_id}{extension}" if extension else f"document_{file_id}",
                "file_type": file_type,
                "file_size": file_size,
                "mapping_id": record_id,
                "source_table": source_table,  # Table that this document belongs to (e.g., "requests", "products", "suppliers")
            }
        
        file_content, content_type = result
        file_type, extension = self._detect_file_type(file_content, download_url)
        file_size = len(file_content)
        
        logger.info(f"✅ Step 1 SUCCESS: Downloaded {file_size} bytes, type: {file_type}, extension: {extension}")
        
        # Step 2: Try to upload to Azure Blob Storage
        logger.info(f"☁️ Step 2: Attempting to upload to Azure Blob Storage: {blob_path}")
        upload_success = await self.azure_blob_service.upload_file(file_content, blob_path, file_type)
        
        if not upload_success:
            logger.warning(f"⚠️ Step 2 FAILED: Could not upload document to Azure: {blob_path}.")
            logger.info(f"   💡 Storing document with Bitrix URL in database (upload failed).")
            
            # Return metadata when upload failed
            # path: Store Bitrix URL data as JSON string (showUrl and downloadUrl dict)
            # url: Store blob storage URL (even if upload failed, we store the intended blob URL)
            # Build blob URL (even if upload failed, we store the intended URL)
            azure_blob_storage_url = getattr(settings, "AZURE_BLOB_STORAGE_URL", None)
            if azure_blob_storage_url:
                azure_blob_storage_url = azure_blob_storage_url.rstrip("/")
                blob_url = f"{azure_blob_storage_url}/{blob_path}"
            else:
                blob_url = blob_path
            
            # Convert url_data dict to JSON string for path field
            path_json = json.dumps(url_data) if isinstance(url_data, dict) else str(url_data)
            
            logger.info(f"   📋 Document metadata: source_table='{source_table}' (belongs to {source_table} table), mapping_id={record_id}")
            return {
                "path": path_json,  # Store Bitrix URL data as JSON string: "{'showUrl': '...', 'downloadUrl': '...'}"
                "url": blob_url,  # Store blob storage URL (Azure blob URL)
                "file_name": f"document_{file_id}{extension}",
                "file_type": file_type,
                "file_size": file_size,
                "mapping_id": record_id,
                "source_table": source_table,  # Table that this document belongs to (e.g., "requests", "products", "suppliers")
            }
        
        logger.info(f"✅ Step 2 SUCCESS: Uploaded to Azure: {blob_path} (size: {file_size} bytes)")
        
        # Step 3: Return document metadata for database insertion with Azure path
        logger.info(f"💾 Step 3: Preparing document metadata for database storage with Azure path: {blob_path}")
        
        # Build Azure blob storage URL for url field
        azure_blob_storage_url = getattr(settings, "AZURE_BLOB_STORAGE_URL", None)
        if azure_blob_storage_url:
            # Remove trailing slash from URL if present
            azure_blob_storage_url = azure_blob_storage_url.rstrip("/")
            # Prepend URL to blob path
            blob_url = f"{azure_blob_storage_url}/{blob_path}"
            logger.debug(f"   Full blob URL with Azure URL: {blob_url}")
        else:
            # If URL not configured, use just the blob path
            blob_url = blob_path
            logger.warning(f"   ⚠️ AZURE_BLOB_STORAGE_URL not configured, storing path without URL prefix")
        
        # Convert url_data dict to JSON string for path field
        # path: Store Bitrix URL data as JSON string (showUrl and downloadUrl dict)
        path_json = json.dumps(url_data) if isinstance(url_data, dict) else str(url_data)
        
        logger.info(f"   📋 Document metadata: source_table='{source_table}' (belongs to {source_table} table), mapping_id={record_id}")
        
        return {
            "path": path_json,  # Store Bitrix URL data as JSON string: "{'showUrl': '...', 'downloadUrl': '...'}"
            "url": blob_url,  # Store blob storage URL (Azure blob URL, e.g., "https://danadairymystotage.blob.core.windows.net/danadairymystotage/uploads/documents/...")
            "file_name": f"document_{file_id}{extension}",
            "file_type": file_type,
            "file_size": file_size,
            "mapping_id": record_id,
            "source_table": source_table,  # Table that this document belongs to (e.g., "requests", "products", "suppliers")
        }

    async def _process_documents(
        self, db: AsyncSession, table_name: str, record_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process all documents from webhook data in parallel."""
        stats = {"total_documents": 0, "documents_processed": 0, "documents_failed": 0}
        
        try:
            logger.info(f"🔍 Starting document processing for {table_name} (ID: {record_id})")
            logger.info(f"🔍 Data structure: keys={list(data.keys())[:30]}, has FIELDS={'FIELDS' in data}, type={type(data)}")
            
            # Handle nested data structure (Bitrix sometimes nests data under FIELDS)
            actual_data = data
            if "FIELDS" in data and isinstance(data["FIELDS"], dict):
                logger.info("📋 Found FIELDS key, using nested data")
                actual_data = data["FIELDS"]
            elif "data" in data and isinstance(data["data"], dict):
                logger.info("📋 Found data key, using nested data")
                actual_data = data["data"]
            
            # Log sample of actual_data to see what we're working with
            sample_keys = list(actual_data.keys())[:30]
            logger.info(f"🔍 Actual data keys (first 30): {sample_keys}")
            
            # Check for document fields in the keys
            doc_field_matches = [k for k in sample_keys if any(doc_field in self._normalize_field_name(k) for doc_field in ["logo", "artwork", "image", "document", "certificate", "keyline", "packing", "technical"])]
            if doc_field_matches:
                logger.info(f"🔍 Potential document fields found: {doc_field_matches}")
            
            table_type = self._get_doc_table_type(table_name)
            if not table_type:
                logger.warning(f"No document table type found for {table_name}")
                return stats
            
            logger.info(f"📋 Table type: {table_type}, Checking for documents in data...")
            documents = self._extract_documents(actual_data, table_type)
            logger.info(f"📄 Extracted {len(documents)} documents from data")
            
            if not documents:
                logger.info(f"No documents found in data for {table_name} (ID: {record_id})")
                return stats
            
            stats["total_documents"] = len(documents)
            source_table = self._normalize_source_table(table_name)
            logger.info(f"📋 Normalized source_table: '{source_table}' (from table_name: '{table_name}')")
            
            # Validate source_table was normalized correctly
            if not source_table:
                logger.error(f"❌ Failed to normalize source_table from table_name: '{table_name}'")
                return stats
            
            tasks = []
            blob_paths = []
            
            for field_name, url_data in documents:
                download_url = url_data.get("downloadUrl") or url_data.get("showUrl")
                if not download_url:
                    logger.warning(f"No download URL found for document field: {field_name}")
                    continue
                
                logger.info(f"📥 Processing document: {field_name} from {download_url}")
                
                # Ensure URL is complete
                if not download_url.startswith("http"):
                    download_url = f"https://dana.bitrix24.eu{download_url}"
                
                parsed = urlparse(download_url)
                file_id = parse_qs(parsed.query).get("fileId", ["unknown"])[0]
                file_type, extension = self._detect_file_type(b"", download_url)
                blob_path = self._generate_blob_path(table_type, record_id, field_name, file_id, extension)
                
                logger.info(f"   File ID: {file_id}, Type: {file_type}, Extension: {extension}")
                logger.info(f"   Azure blob path: {blob_path}")
                
                # Store actual blob path for checking existence
                blob_paths.append(blob_path)
                
                tasks.append(self._process_single_document(
                    db, table_type, record_id, source_table, field_name, url_data, blob_path
                ))
            
            # Check for existing documents
            existing_map = await self._check_documents_exist(db, blob_paths, record_id, source_table)
            
            tasks_to_process = []
            for i, (task, blob_path) in enumerate(zip(tasks, blob_paths)):
                if not existing_map.get(blob_path, False):
                    tasks_to_process.append(task)
                else:
                    stats["documents_processed"] += 1
            
            if tasks_to_process:
                logger.info(f"📥 Processing {len(tasks_to_process)} new documents (downloading and uploading)...")
                results = await asyncio.gather(*tasks_to_process, return_exceptions=True)
                
                new_documents = []
                failed_count = 0
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        failed_count += 1
                        stats["documents_failed"] += 1
                        logger.error(f"❌ Document processing error #{i+1}: {result}", exc_info=True)
                    elif result:
                        new_documents.append(result)
                        stats["documents_processed"] += 1
                        # Check if document was stored with Bitrix URL (download/upload failed) or Azure path (success)
                        path_value = result.get("path", "")
                        if path_value.startswith("http") and "blob.core.windows.net" not in path_value:
                            logger.info(f"⚠️ Document #{i+1} stored with Bitrix URL (download/upload failed): {result.get('file_name', 'unknown')}")
                        else:
                            logger.debug(f"✅ Document #{i+1} processed successfully with Azure path: {result.get('file_name', 'unknown')}")
                    else:
                        failed_count += 1
                        stats["documents_failed"] += 1
                        logger.warning(f"⚠️ Document #{i+1} returned None (unexpected error)")
                
                logger.info(f"📊 Document processing summary: {len(new_documents)} documents to store, {failed_count} errors out of {len(tasks_to_process)} total")
                
                if new_documents:
                    logger.info(f"💾 Step 3: Inserting {len(new_documents)} new documents into database for {table_name} (ID: {record_id})")
                    logger.info(f"   📋 Documents will be stored in database (some may have Bitrix URLs if download/upload failed)")
                    
                    # Validate outer scope source_table is set
                    if not source_table or source_table.strip() == "":
                        logger.error(f"   ❌ CRITICAL ERROR: Outer scope source_table is empty! table_name='{table_name}'")
                        logger.error(f"      Attempting to re-normalize from table_name...")
                        source_table = self._normalize_source_table(table_name)
                        logger.warning(f"      Re-normalized source_table: '{source_table}'")
                        if not source_table or source_table.strip() == "":
                            logger.error(f"      ❌ Re-normalization failed! Using fallback 'requests'")
                            source_table = "requests"
                    
                    logger.info(f"   📋 Using source_table: '{source_table}' (type: {type(source_table)}, len: {len(source_table) if source_table else 0}) for all documents in this batch")
                    inserted_count = 0
                    for doc in new_documents:
                        # Ensure source_table is always set in document dict (add if missing)
                        if "source_table" not in doc or not doc.get("source_table") or (isinstance(doc.get("source_table"), str) and doc.get("source_table").strip() == ""):
                            doc["source_table"] = source_table
                            logger.debug(f"   🔧 Added missing source_table '{source_table}' to document dict")
                        
                        try:
                            path_value = doc.get("path")
                            
                            # Validate that path is not None (should never happen, but double-check)
                            if not path_value:
                                logger.error(f"   ❌ SKIPPING: Document {doc['file_name']} has NULL path - this should not happen!")
                                logger.error(f"      This document was not uploaded to Azure. Skipping database insertion.")
                                stats["documents_failed"] += 1
                                continue
                            
                            # Validate and get source_table (required field)
                            # First try to get from document dict, then fallback to outer scope source_table
                            source_table_value = doc.get("source_table")
                            if not source_table_value or (isinstance(source_table_value, str) and source_table_value.strip() == ""):
                                logger.warning(f"   ⚠️ Document {doc.get('file_name', 'unknown')} missing source_table in dict, using outer scope value")
                                logger.warning(f"      Document data keys: {list(doc.keys())}")
                                # Use the source_table from outer scope (normalized earlier in _process_documents)
                                source_table_value = source_table  # Use the normalized source_table from outer scope
                                logger.info(f"   ✅ Using source_table from outer scope: '{source_table_value}'")
                            
                            # Final validation
                            if not source_table_value or (isinstance(source_table_value, str) and source_table_value.strip() == ""):
                                logger.error(f"   ❌ SKIPPING: Document {doc.get('file_name', 'unknown')} - source_table is still empty after fallback")
                                logger.error(f"      This should not happen. Check _normalize_source_table function.")
                                stats["documents_failed"] += 1
                                continue
                            
                            # Check if path is Azure blob URL or Bitrix URL
                            path_type = "Azure path" if "blob.core.windows.net" in path_value else "Bitrix URL"
                            logger.info(f"   📄 Inserting document: {doc['file_name']} ({path_type}: {path_value[:100]}...)")
                            logger.info(f"      📋 source_table: '{source_table_value}' (document belongs to {source_table_value} table), mapping_id: {doc['mapping_id']}")
                            
                            # Store full URL (no truncation - path and url columns are now Text type)
                            url_value = doc.get("url", "")
                            
                            # Truncate other string fields if needed (file_name and file_type are still String(255))
                            file_name_value = doc.get("file_name", "")[:255] if doc.get("file_name") else None
                            file_type_value = doc.get("file_type", "")[:255] if doc.get("file_type") else None
                            # Store full path with Azure URL (no truncation - path column is now Text type)
                            path_value_full = path_value if path_value else None
                            
                            # Validate required fields
                            if not path_value_full:
                                logger.error(f"   ❌ SKIPPING: Document {file_name_value} has NULL or empty path")
                                stats["documents_failed"] += 1
                                continue
                            
                            if not doc.get("mapping_id"):
                                logger.error(f"   ❌ SKIPPING: Document {file_name_value} has NULL mapping_id")
                                stats["documents_failed"] += 1
                                continue
                            
                            # Final check: ensure source_table_value is set (use outer scope source_table as ultimate fallback)
                            if not source_table_value or source_table_value is None or (isinstance(source_table_value, str) and source_table_value.strip() == ""):
                                source_table_value = source_table
                                logger.warning(f"   ⚠️ source_table_value was empty/None, using outer scope source_table: '{source_table_value}'")
                            
                            # Ensure source_table_value is a non-empty string
                            if not source_table_value or source_table_value is None:
                                source_table_value = source_table if source_table else "requests"  # Ultimate fallback
                                logger.error(f"   ❌ CRITICAL: source_table_value is still None/empty, using fallback: '{source_table_value}'")
                            
                            # Convert to string and strip whitespace
                            source_table_value = str(source_table_value).strip()
                            if not source_table_value:
                                source_table_value = str(source_table) if source_table else "requests"
                                logger.error(f"   ❌ CRITICAL: source_table_value is empty after conversion, using: '{source_table_value}'")
                            
                            logger.info(f"   🔍 FINAL CHECK - Inserting with source_table: '{source_table_value}' (type: {type(source_table_value)}, len: {len(source_table_value)})")
                            
                            # Prepare insert parameters
                            insert_params = {
                                "path": path_value_full,
                                "url": url_value if url_value else None,
                                "file_name": file_name_value,
                                "file_type": file_type_value,
                                "file_size": doc.get("file_size") or 0,
                                "source": "bitrix",
                                "mapping_id": doc["mapping_id"],
                                "source_table": source_table_value,  # Use validated source_table (guaranteed to be non-empty string)
                            }
                            
                            # Log all parameters for debugging
                            logger.info(f"   🔍 INSERT parameters: source_table='{insert_params['source_table']}', mapping_id={insert_params['mapping_id']}, source='{insert_params['source']}'")
                            logger.debug(f"   🔍 Full insert params: {list(insert_params.keys())}")
                            
                            result = await db.execute(
                                text("""
                                    INSERT INTO `documents` 
                                    (`path`, `url`, `file_name`, `file_type`, `file_size`, `source`, `mapping_id`, `source_table`, `created_at`, `updated_at`)
                                    VALUES (:path, :url, :file_name, :file_type, :file_size, :source, :mapping_id, :source_table, NOW(), NOW())
                                """),
                                insert_params,
                            )
                            
                            # Verify the insert was successful
                            if result.rowcount and result.rowcount > 0:
                                inserted_count += 1
                                logger.info(f"   ✅ Successfully inserted document: {file_name_value} -> {path_value_full[:100]}... (rowcount: {result.rowcount})")
                            else:
                                logger.warning(f"   ⚠️ Insert executed but rowcount is 0 for document: {file_name_value}")
                                stats["documents_failed"] += 1
                                
                        except Exception as insert_error:
                            error_msg = str(insert_error)
                            logger.error(f"   ❌ Failed to insert document {doc.get('file_name', 'unknown')}: {error_msg}", exc_info=True)
                            
                            # Check for specific error types
                            if "Data too long" in error_msg or "1406" in error_msg:
                                logger.error(f"      💡 Field value too long for column. Check path, url, file_name, or file_type length.")
                            elif "Duplicate entry" in error_msg or "1062" in error_msg:
                                logger.warning(f"      💡 Document already exists (duplicate), skipping.")
                                stats["documents_processed"] += 1  # Count as processed, not failed
                            elif "Cannot add or update" in error_msg or "1452" in error_msg:
                                logger.error(f"      💡 Foreign key constraint violation. Check mapping_id and source_table.")
                            else:
                                logger.error(f"      💡 Unknown database error. Check logs above for details.")
                            
                            stats["documents_failed"] += 1
                    
                    # Flush to ensure inserts are in the transaction (will be committed with main transaction)
                    try:
                        await db.flush()
                        logger.info(f"✅ Successfully flushed {inserted_count} documents to database (all with Azure paths)")
                    except Exception as flush_error:
                        logger.error(f"❌ Failed to flush documents to database: {flush_error}", exc_info=True)
                        stats["documents_failed"] += inserted_count
                        stats["documents_processed"] -= inserted_count
                else:
                    logger.warning(f"⚠️ No documents to insert (all downloads/uploads failed or documents already exist)")
            
            logger.info(
                f"Documents processed for {table_name} (ID: {record_id}): "
                f"{stats['documents_processed']}/{stats['total_documents']} successful"
            )
            
        except Exception as e:
            logger.error(f"Error processing documents for {table_name} (ID: {record_id}): {e}", exc_info=True)
        finally:
            if self._doc_session and not self._doc_session.closed:
                await self._doc_session.close()
        
        return stats

    async def process_webhook_data(
        self,
        db: AsyncSession,
        eventtype: str,
        table: str,
        data: Dict[str, Any],
        bitrix_id: Optional[str] = None,
        mapping: Optional[List[Dict[str, Any]]] = None,
        webhook: str = "bitrix",
    ) -> Dict[str, Any]:
        """
        Process webhook data based on eventtype (insert, update, delete).
        
        Args:
            db: Database session
            eventtype: Operation type (insert, update, delete)
            table: Table name
            data: Table data
            bitrix_id: Bitrix ID
            mapping: Mapping data for bridge tables (list format)
            webhook: Webhook source (bitrix or outlook)
        
        Returns:
            Response data
        """
        try:
            eventtype_lower = eventtype.lower()
            table_lower = table.lower()

            logger.info(f"Processing webhook data: {eventtype_lower} for {table_lower} (webhook: {webhook})")

            if eventtype_lower == "insert":
                result = await self.insert(db, table_lower, data, bitrix_id, mapping)
                logger.info(f"✅ INSERT operation completed for {table_lower}")
            elif eventtype_lower == "update":
                result = await self.update(db, table_lower, data, bitrix_id, mapping)
                logger.info(f"✅ UPDATE operation completed for {table_lower}")
            elif eventtype_lower == "delete":
                result = await self.delete_record(db, table_lower, bitrix_id)
                logger.info(f"✅ DELETE operation completed for {table_lower} (type: {result.get('delete_type', 'unknown')})")
            else:
                raise ValueError(f"Unsupported eventtype: {eventtype}. Must be insert, update, or delete")

            return {
                "eventtype": eventtype_lower,
                "table": table_lower,
                "webhook": webhook,
                "data": result,
            }

        except Exception as exc:
            logger.error(f"Error processing webhook data: {exc}", exc_info=True)
            raise

    


