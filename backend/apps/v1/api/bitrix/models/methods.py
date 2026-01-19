"""
Helper methods and SQL queries for Bitrix24 webhook processing.
All database queries and helper methods without loops.
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, unquote

from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.bitrix.schema import BitrixWebhookRequest
from apps.v1.api.products.models.model import Products
from apps.v1.api.suppliers.models.model import Suppliers, ProductSupplierMapping
from apps.v1.api.customer.models.model import Customers
from apps.v1.api.request.models.model import Requests, RequestCustomersMapping, Stage, RequestStageActivity
from apps.v1.api.logistic.models.model import Logistic
from apps.v1.api.auth.models.model import Users, Modules, ActivityLog
from apps.v1.api.auth.models.attribute import Action

logger = logging.getLogger(__name__)


class BitrixWebhookMethods:
    """Helper class for Bitrix24 webhook processing methods and SQL queries."""

    @staticmethod
    def parse_form_data(body_str: str) -> dict:
        """Parse form-urlencoded data to nested dictionary without loops."""
        form_data = parse_qs(body_str, keep_blank_values=True)
        raw_body = {}
        
        # Use dict comprehension and map instead of loop
        processed_items = map(
            lambda item: BitrixWebhookMethods._process_form_item(item, raw_body),
            form_data.items()
        )
        list(processed_items)  # Execute the map
        
        return raw_body
    
    @staticmethod
    def _process_form_item(item: Tuple[str, List[str]], raw_body: dict) -> None:
        """Process a single form item."""
        key, value_list = item
        unquoted_key = unquote(key)
        value = unquote(value_list[0]) if value_list else ""
        
        if "[" in unquoted_key and "]" in unquoted_key:
            parts = unquoted_key.split("[")
            root_key = parts[0]
            nested_keys = [part.rstrip("]") for part in parts[1:]]
            
            current = raw_body.setdefault(root_key, {})
            # Build nested structure using reduce pattern
            for nested_key in nested_keys[:-1]:
                current = current.setdefault(nested_key, {})
            current[nested_keys[-1]] = value
        else:
            if unquoted_key in ("data", "auth") and value:
                try:
                    raw_body[unquoted_key] = json.loads(value)
                except json.JSONDecodeError:
                    raw_body[unquoted_key] = value
            else:
                raw_body[unquoted_key] = value

    @staticmethod
    def extract_event_from_path(path: str) -> Optional[str]:
        """Extract event from path without loops."""
        parts = path.split("/")
        matching_parts = [part for part in parts if part.startswith("ON") and len(part) > 5]
        return matching_parts[0] if matching_parts else None

    @staticmethod
    def extract_product_id(webhook_data: BitrixWebhookRequest) -> Optional[str]:
        """Extract product ID from webhook data."""
        data = webhook_data.data

        if isinstance(data, dict):
            fields = data.get("FIELDS") or data
            if isinstance(fields, dict):
                return str(fields.get("ID") or fields.get("id") or fields.get("Id") or "")

        elif isinstance(data, list) and data:
            item = data[0]
            if isinstance(item, dict):
                return str(item.get("ID") or item.get("id") or item.get("Id") or "")

        elif isinstance(data, str):
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    fields = parsed.get("FIELDS") or parsed
                    if isinstance(fields, dict):
                        return str(fields.get("ID") or fields.get("id") or fields.get("Id") or "")
            except json.JSONDecodeError:
                pass

        return None

    # Database Query Methods

    @staticmethod
    async def get_existing_db_columns(db: AsyncSession, table_name: str) -> Set[str]:
        """Get actual database columns for a table."""
        try:
            result = await db.execute(
                text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = :table_name
                """),
                {"table_name": table_name}
            )
            columns = {row[0] for row in result.fetchall()}
            logger.info(f"Found {len(columns)} columns in database table {table_name}")
            return columns
        except Exception as e:
            logger.error(f"Could not query database columns for {table_name}: {e}", exc_info=True)
            return set()
    
    @staticmethod
    async def get_model_columns(model_class: Any) -> Set[str]:
        """Get all column names from a SQLAlchemy model."""
        return {col.name for col in model_class.__table__.columns}
    
    @staticmethod
    async def get_nonexistent_model_columns(
        db: AsyncSession, model_class: Any, table_name: Optional[str] = None
    ) -> Set[str]:
        """
        Get columns that exist in the model but not in the database.
        This helps identify fields that need to be filtered out.
        """
        if table_name is None:
            table_name = model_class.__tablename__
        
        model_columns = await BitrixWebhookMethods.get_model_columns(model_class)
        db_columns = await BitrixWebhookMethods.get_existing_db_columns(db, table_name)
        
        nonexistent = model_columns - db_columns
        if nonexistent:
            logger.warning(
                f"Model {model_class.__name__} has {len(nonexistent)} columns not in database: {nonexistent}"
            )
        return nonexistent

    @staticmethod
    async def get_product_by_bitrix_id(db: AsyncSession, bitrix_id: str) -> Optional[Products]:
        """Get product by bitrix_id."""
        try:
            stmt = select(Products).where(Products.bitrix_id == int(bitrix_id))
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except (ValueError, TypeError):
            return None

    @staticmethod
    async def get_product_id_by_bitrix_id(db: AsyncSession, bitrix_id: str) -> Optional[int]:
        """Get product database ID by bitrix_id using raw SQL."""
        result = await db.execute(
            text("SELECT id FROM products WHERE bitrix_id = :bitrix_id LIMIT 1"),
            {"bitrix_id": str(bitrix_id)}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def get_product_id_by_db_id(db: AsyncSession, product_id: int) -> Optional[int]:
        """Get product database ID by database ID (validation)."""
        result = await db.execute(
            text("SELECT id FROM products WHERE id = :product_id LIMIT 1"),
            {"product_id": product_id}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def get_supplier_id_by_bitrix_id(db: AsyncSession, bitrix_id: str) -> Optional[int]:
        """Get supplier database ID by bitrix_id."""
        result = await db.execute(
            text("SELECT id FROM suppliers WHERE bitrix_id = :bitrix_id LIMIT 1"),
            {"bitrix_id": str(bitrix_id)}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def get_supplier_id_by_db_id(db: AsyncSession, supplier_id: int) -> Optional[int]:
        """Get supplier database ID by database ID (validation)."""
        stmt = select(Suppliers.id).where(Suppliers.id == supplier_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_customer_id_by_bitrix_id(db: AsyncSession, bitrix_id: str) -> Optional[int]:
        """Get customer database ID by bitrix_id."""
        try:
            stmt = select(Customers.id).where(Customers.bitrix_id == str(bitrix_id))
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            return None

    @staticmethod
    async def get_request_id_by_bitrix_id(db: AsyncSession, bitrix_id: str) -> Optional[int]:
        """Get request database ID by bitrix_id."""
        stmt = select(Requests.id).where(Requests.bitrix_id == str(bitrix_id))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_logistic_id_by_product_id(db: AsyncSession, product_id: int) -> Optional[int]:
        """Get logistic ID by product_id."""
        result = await db.execute(
            text("SELECT id FROM logistic WHERE product_id = :product_id LIMIT 1"),
            {"product_id": product_id}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def get_logistic_by_id(db: AsyncSession, logistic_id: int) -> Optional[Logistic]:
        """Get logistic record by ID."""
        stmt = select(Logistic).where(Logistic.id == logistic_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def check_product_supplier_mapping_exists(
        db: AsyncSession, supplier_id: int, product_id: int
    ) -> Optional[ProductSupplierMapping]:
        """Check if product_supplier mapping exists."""
        stmt = select(ProductSupplierMapping).where(
            ProductSupplierMapping.supplier_id == supplier_id,
            ProductSupplierMapping.product_id == product_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def check_request_customer_mapping_exists(
        db: AsyncSession, customer_id: int, request_id: int
    ) -> Optional[RequestCustomersMapping]:
        """Check if request_customer mapping exists."""
        stmt = select(RequestCustomersMapping).where(
            RequestCustomersMapping.customer_id == customer_id,
            RequestCustomersMapping.request_id == request_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def check_request_product_mapping_exists(
        db: AsyncSession, request_id: int, product_id: int
    ) -> Optional[int]:
        """Check if request_product mapping exists."""
        result = await db.execute(
            text("SELECT id FROM request_products WHERE request_id = :request_id AND product_id = :product_id LIMIT 1"),
            {"request_id": request_id, "product_id": product_id}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def insert_request_product_mapping(
        db: AsyncSession, request_id: int, product_id: int
    ) -> None:
        """Insert request_product mapping."""
        await db.execute(
            text("INSERT INTO request_products (request_id, product_id, created_at, updated_at) VALUES (:request_id, :product_id, NOW(), NOW())"),
            {"request_id": request_id, "product_id": product_id}
        )

    @staticmethod
    async def update_logistic_by_id(
        db: AsyncSession, logistic_id: int, update_fields: List[str], update_params: Dict[str, Any]
    ) -> None:
        """Update logistic record using raw SQL."""
        update_sql = text(f"UPDATE logistic SET {', '.join(update_fields)} WHERE id = :logistic_id")
        update_params["logistic_id"] = logistic_id
        await db.execute(update_sql, update_params)

    @staticmethod
    async def get_record_id_by_bitrix_id(
        db: AsyncSession, table_name: str, bitrix_id: str, include_deleted: bool = False
    ) -> Optional[int]:
        """Get record ID by bitrix_id from any table."""
        # Normalize table name (singular to plural, handle aliases)
        table_lower = table_name.lower()
        actual_table_name = table_name
        
        # Map singular/alias names to actual database table names
        if table_lower in ["request", "deal", "deals"]:
            actual_table_name = "requests"
        elif table_lower in ["company", "supplier"]:
            actual_table_name = "suppliers"
        elif table_lower in ["customer", "contact", "contacts"]:
            actual_table_name = "customers"
        elif table_lower == "product":
            actual_table_name = "products"
        elif table_lower in ["category", "product_section"]:
            actual_table_name = "categories"
        elif table_lower == "user":
            actual_table_name = "users"
        
        # Handle zero dates - MySQL doesn't accept '0000-00-00 00:00:00' in direct comparisons
        # A record is "not deleted" if deleted_at is NULL or is a zero date (YEAR = 0)
        deleted_condition = "" if include_deleted else "AND (deleted_at IS NULL OR YEAR(deleted_at) = 0)"
        result = await db.execute(
            text(f"SELECT id FROM `{actual_table_name}` WHERE bitrix_id = :bitrix_id {deleted_condition} LIMIT 1"),
            {"bitrix_id": bitrix_id}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def soft_delete_record(db: AsyncSession, table_name: str, record_id: int) -> int:
        """Soft delete a record by setting deleted_at."""
        result = await db.execute(
            text(f"UPDATE `{table_name}` SET deleted_at = UTC_TIMESTAMP() WHERE id = :record_id"),
            {"record_id": record_id}
        )
        return result.rowcount

    @staticmethod
    async def verify_deleted_at(db: AsyncSession, table_name: str, record_id: int) -> Optional[datetime]:
        """Verify deleted_at was set."""
        result = await db.execute(
            text(f"SELECT deleted_at FROM `{table_name}` WHERE id = :record_id"),
            {"record_id": record_id}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def delete_request_products_mappings(db: AsyncSession, request_id: int) -> int:
        """Delete all request_products mappings for a request."""
        result = await db.execute(
            text("DELETE FROM request_products WHERE request_id = :record_id"),
            {"record_id": request_id}
        )
        return result.rowcount

    @staticmethod
    async def delete_request_customers_mappings(db: AsyncSession, request_id: int) -> int:
        """Delete all request_customers mappings for a request."""
        result = await db.execute(
            text("DELETE FROM request_customers WHERE request_id = :record_id"),
            {"record_id": request_id}
        )
        return result.rowcount

    @staticmethod
    async def delete_product_suppliers_mappings_by_supplier(db: AsyncSession, supplier_id: int) -> int:
        """Delete all product_suppliers mappings for a supplier."""
        result = await db.execute(
            text("DELETE FROM product_suppliers WHERE supplier_id = :record_id"),
            {"record_id": supplier_id}
        )
        return result.rowcount

    @staticmethod
    async def delete_product_suppliers_mappings_by_product(db: AsyncSession, product_id: int) -> int:
        """Delete all product_suppliers mappings for a product."""
        result = await db.execute(
            text("DELETE FROM product_suppliers WHERE product_id = :record_id"),
            {"record_id": product_id}
        )
        return result.rowcount

    @staticmethod
    async def delete_request_customers_mappings_by_customer(db: AsyncSession, customer_id: int) -> int:
        """Delete all request_customers mappings for a customer."""
        result = await db.execute(
            text("DELETE FROM request_customers WHERE customer_id = :record_id"),
            {"record_id": customer_id}
        )
        return result.rowcount

    @staticmethod
    async def delete_request_products_mappings_by_product(db: AsyncSession, product_id: int) -> int:
        """Delete all request_products mappings for a product."""
        result = await db.execute(
            text("DELETE FROM request_products WHERE product_id = :record_id"),
            {"record_id": product_id}
        )
        return result.rowcount

    @staticmethod
    async def update_requests_company_id_to_null(db: AsyncSession, company_id: int) -> int:
        """Update requests to set company_id = NULL."""
        result = await db.execute(
            text("UPDATE requests SET company_id = NULL WHERE company_id = :record_id"),
            {"record_id": company_id}
        )
        return result.rowcount

    @staticmethod
    async def check_deal_id_exists(db: AsyncSession, deal_id: str, exclude_request_id: Optional[int] = None) -> Optional[int]:
        """Check if deal_id already exists."""
        if exclude_request_id:
            result = await db.execute(
                text("SELECT id FROM requests WHERE deal_id = :deal_id AND id != :request_id LIMIT 1"),
                {"deal_id": deal_id, "request_id": exclude_request_id}
            )
        else:
            result = await db.execute(
                text("SELECT id FROM requests WHERE deal_id = :deal_id LIMIT 1"),
                {"deal_id": deal_id}
            )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def update_deal_id(db: AsyncSession, request_id: int, deal_id: str, table_name: str = "requests") -> None:
        """Update deal_id for a request."""
        await db.execute(
            text(f"UPDATE `{table_name}` SET `deal_id` = :deal_id WHERE id = :request_id"),
            {"deal_id": deal_id, "request_id": request_id}
        )

    @staticmethod
    async def get_request_data_for_deal_id(
        db: AsyncSession, request_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get request data needed for deal_id generation."""
        result = await db.execute(
            text("""
                SELECT 
                    pi_number, name, company_id, port_of_discharge, inquiry_date,
                    bitrix_id
                FROM requests 
                WHERE id = :request_id
                LIMIT 1
            """),
            {"request_id": request_id}
        )
        row = result.fetchone()
        if row:
            return {
                "pi_number": row[0] if row[0] else "",
                "name": row[1] if row[1] else "",
                "company_id": row[2] if row[2] else None,
                "port_of_discharge": row[3] if row[3] else "",
                "inquiry_date": row[4] if row[4] else None,
                "bitrix_id": row[5] if row[5] else None,
            }
        return None

    @staticmethod
    async def get_client_name_by_company_id(db: AsyncSession, company_id: int) -> Optional[str]:
        """Get client name (company_name or supplier_name) by company_id."""
        result = await db.execute(
            text("SELECT company_name, supplier_name FROM suppliers WHERE id = :company_id LIMIT 1"),
            {"company_id": company_id}
        )
        row = result.fetchone()
        if row:
            return (row[0] or row[1] or "").strip()
        return None

    @staticmethod
    async def get_product_name_by_request_id(db: AsyncSession, request_id: int) -> Optional[str]:
        """Get product name for a request."""
        result = await db.execute(
            text("""
                SELECT p.name
                FROM request_products rp
                JOIN products p ON rp.product_id = p.id
                WHERE rp.request_id = :request_id
                LIMIT 1
            """),
            {"request_id": request_id}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def get_deal_id_by_request_id(db: AsyncSession, request_id: int) -> Optional[str]:
        """Get deal_id for a request."""
        result = await db.execute(
            text("SELECT deal_id FROM requests WHERE id = :request_id LIMIT 1"),
            {"request_id": request_id}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def get_user_id_by_bitrix_id(db: AsyncSession, bitrix_id: int) -> Optional[int]:
        """Get user database ID by bitrix_id."""
        stmt = select(Users.id).where(Users.bitrix_id == bitrix_id).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_module_id_for_requests(db: AsyncSession) -> Optional[int]:
        """Get module_id for requests module."""
        stmt = select(Modules.id).where(
            (Modules.name.ilike("%request%")) | (Modules.name.ilike("%deal%"))
        ).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_record_by_bitrix_id_orm(
        db: AsyncSession, model: Any, bitrix_id: str
    ) -> Optional[Any]:
        """Get record by bitrix_id using ORM."""
        stmt = select(model).where(model.bitrix_id == bitrix_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # Helper methods without loops
    
    @staticmethod
    def filter_nonexistent_columns(
        data: Dict[str, Any], existing_columns: Set[str], known_nonexistent: Set[str] = None
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Filter out columns that don't exist in database without loops.
        
        Args:
            data: Data dictionary to filter
            existing_columns: Set of columns that exist in the database
            known_nonexistent: Set of known columns that don't exist (for additional filtering)
        
        Returns:
            Tuple of (filtered_data, skipped_columns)
        """
        # Note: priority is now in the database, so it's not in the default exclusion list
        known_nonexistent = known_nonexistent or set()
        
        # Filter: keep only columns that exist in database AND are not in known_nonexistent
        filtered_data = {
            k: v for k, v in data.items()
            if k not in known_nonexistent and k in existing_columns
        }
        
        skipped_columns = [
            k for k in data.keys()
            if k in known_nonexistent or k not in existing_columns
        ]
        
        if skipped_columns:
            logger.info(f"Skipped {len(skipped_columns)} columns that don't exist in database: {skipped_columns}")
        
        return filtered_data, skipped_columns

    @staticmethod
    def remove_nonexistent_columns(data: Dict[str, Any], known_nonexistent: Set[str] = None) -> Dict[str, Any]:
        """
        Remove known nonexistent columns without loops.
        
        Args:
            data: Data dictionary to filter
            known_nonexistent: Set of columns that don't exist in database
        
        Returns:
            Filtered data dictionary
        """
        # No columns are excluded by default - allow all columns
        # Extra columns that don't exist will be handled gracefully by the database
        known_nonexistent = known_nonexistent or set()
        return {k: v for k, v in data.items() if k not in known_nonexistent}

    @staticmethod
    def extract_partial_shipment(name: str) -> str:
        """Extract partial shipment info from name without loops."""
        match = re.search(r'\((\d+)/(\d+)\)', name) if name else None
        return f" ({match.group(1)}/{match.group(2)})" if match else ""

    @staticmethod
    def extract_order_sequence(name: str) -> str:
        """Extract order sequence from name without loops."""
        match = re.search(r'#(\d+)/(\d+)', name) if name else None
        return f"#{match.group(1)}/{match.group(2)}" if match else ""

    @staticmethod
    def set_default_values_for_fields(
        data: Dict[str, Any], field_defaults: Dict[str, Any], is_insert: bool = True
    ) -> Dict[str, Any]:
        """Set default values for fields without loops."""
        result = data.copy()
        
        # Use dict comprehension to set defaults
        defaults_to_apply = {
            k: v for k, v in field_defaults.items()
            if (is_insert or k in data) and result.get(k) is None
        }
        result.update(defaults_to_apply)
        
        return result

    @staticmethod
    async def soft_delete_product_by_bitrix_id(db: AsyncSession, bitrix_id: str) -> int:
        """
        Soft delete product by bitrix_id using SQL query.
        
        SQL: UPDATE products SET active = False, deleted_at = :current_time 
             WHERE bitrix_id = :bitrix_id
        
        Args:
            db: Database session
            bitrix_id: Bitrix product ID
            
        Returns:
            int: Number of rows affected
        """
        stmt = (
            update(Products)
            .where(Products.bitrix_id == int(bitrix_id))
            .values(active=False, deleted_at=datetime.utcnow())
        )
        result = await db.execute(stmt)
        return result.rowcount

    @staticmethod
    async def generate_deal_id(
        data: Dict[str, Any], db: Optional[AsyncSession] = None, request_id: Optional[int] = None
    ) -> str:
        """
        Generate deal_id based on the structure:
        "PI Number (Partial Shipment) - Client Name - Product Name - Quantity - Destination Port - Order Sequence"
        
        Example: "DU171008 (1/3) - Zhejiang Int. - UHT 250ml - 3x20' - Ningbo - #1/2018"
        
        Args:
            data: Request data dictionary
            db: Database session (optional, for querying related data)
            request_id: Request ID (optional, for querying related products after insert)
            
        Returns:
            Generated deal_id string
        """
        # If request_id is provided, fetch the full record from database to get all actual values
        if request_id and db:
            try:
                request_data = await BitrixWebhookMethods.get_request_data_for_deal_id(db, request_id)
                if request_data:
                    # Merge database data with provided data (provided data takes precedence)
                    merged_data = {**request_data, **{k: v for k, v in data.items() if v is not None and v != ""}}
                    data = merged_data
            except Exception as e:
                logger.warning(f"Could not fetch request data for request_id {request_id}: {e}")
        
        components = []
        
        # 1. PI Number (with optional Partial Shipment)
        pi_number = data.get("pi_number") or ""
        if isinstance(pi_number, str):
            pi_number = pi_number.strip()
        else:
            pi_number = str(pi_number).strip() if pi_number else ""
        if pi_number:
            # Check if name contains partial shipment info like "(1/3)"
            name = data.get("name", "")
            partial_shipment = BitrixWebhookMethods.extract_partial_shipment(name)
            components.append(f"{pi_number}{partial_shipment}")
        else:
            components.append("N/A")
        
        # 2. Client Name
        client_name = ""
        company_id = data.get("company_id")
        if company_id and db:
            try:
                client_name = await BitrixWebhookMethods.get_client_name_by_company_id(db, company_id)
            except Exception as e:
                logger.warning(f"Could not fetch client name for company_id {company_id}: {e}")
        
        # Fallback: try to extract from name field
        if not client_name:
            name = data.get("name") or ""
            if isinstance(name, str) and " - " in name:
                parts = name.split(" - ")
                if len(parts) >= 2:
                    client_name = parts[1].strip()
        
        if not client_name:
            client_name = "N/A"
        
        components.append(client_name)
        
        # 3. Product Name and Quantity
        product_name = "N/A"
        quantity = "N/A"
        
        if request_id and db:
            try:
                product_name = await BitrixWebhookMethods.get_product_name_by_request_id(db, request_id) or "N/A"
            except Exception as e:
                logger.warning(f"Could not fetch product info for request_id {request_id}: {e}")
        
        # Fallback: try to extract from name field
        if product_name == "N/A":
            name = data.get("name", "")
            if name and " - " in name:
                parts = name.split(" - ")
                if len(parts) >= 3:
                    product_name = parts[2].strip()
                if len(parts) >= 4:
                    quantity = parts[3].strip()
        
        components.append(product_name)
        components.append(quantity)
        
        # 4. Destination Port
        port_of_discharge = data.get("port_of_discharge") or ""
        if isinstance(port_of_discharge, str):
            port_of_discharge = port_of_discharge.strip()
        else:
            port_of_discharge = str(port_of_discharge).strip() if port_of_discharge else ""
        
        if port_of_discharge:
            components.append(port_of_discharge)
        else:
            components.append("N/A")
        
        # 5. Order Sequence
        order_sequence = BitrixWebhookMethods.extract_order_sequence(data.get("name", ""))
        
        if not order_sequence:
            # Generate order sequence from inquiry_date or current year
            inquiry_date = data.get("inquiry_date")
            if inquiry_date:
                if isinstance(inquiry_date, str):
                    try:
                        inquiry_date = datetime.fromisoformat(inquiry_date.replace('Z', '+00:00'))
                    except:
                        inquiry_date = datetime.now()
                elif not isinstance(inquiry_date, datetime):
                    inquiry_date = datetime.now()
            else:
                inquiry_date = datetime.now()
            
            year = inquiry_date.year
            order_sequence = f"#1/{year}"
        
        components.append(order_sequence)
        
        # Join all components with " - "
        deal_id = " - ".join(components)
        
        # Always make deal_id unique by appending bitrix_id or request_id
        unique_suffix = ""
        if request_id:
            unique_suffix = f" - ID:{request_id}"
        elif data.get("bitrix_id"):
            unique_suffix = f" - BX:{data.get('bitrix_id')}"
        else:
            unique_suffix = f" - TS:{int(time.time() * 1000)}"
        
        deal_id = deal_id + unique_suffix
        
        return deal_id

    @staticmethod
    def set_default_values_for_required_fields(table_name: str, data: Dict[str, Any], is_insert: bool = True) -> Dict[str, Any]:
        """
        Set default values for required fields that cannot be null.
        This is especially important for requests table when data comes from AI function.
        
        Args:
            table_name: Name of the table
            data: Data dictionary to process
            is_insert: True for insert operations, False for update operations
        
        Returns:
            Data dictionary with default values set for required fields
        """
        table_lower = table_name.lower()
        
        if table_lower not in ["request", "requests", "deal", "deals"]:
            return data
        
        # Numeric field definitions (Integer and Float)
        numeric_fields = {
            "probability", "advance_payment", "lead_rank", "contact_id", "estimate_id",
            "moved_by_id", "repeat_sale_segment_id", "last_activity_by",
            "loaded_container_quantity", "week_commitment", "estimated_volume",
            "created_by", "modified_by", "freight_charges", "total", "tax_rate",
            "item_id_in_data_source"
        }
        
        # Normalize empty strings to None for numeric fields (MySQL doesn't accept empty strings for numeric columns)
        for field in numeric_fields:
            if field in data:
                value = data.get(field)
                if value == "" or (isinstance(value, str) and value.strip() == ""):
                    data[field] = None
        
        # Integer/Float field defaults
        numeric_defaults = {
            "probability": 0,
            "advance_payment": 0.0,
            "lead_rank": 0,
            "contact_id": 0,
            "estimate_id": 0,
            "moved_by_id": 0,
            "repeat_sale_segment_id": 0,
            "last_activity_by": 0,
            "loaded_container_quantity": 0,
            "week_commitment": 0,
            "estimated_volume": 0,
            "created_by": 0,
            "modified_by": 0,
            "freight_charges": 0.0,
            "total": 0.0,
            "tax_rate": 0.0,
        }
        
        # Apply numeric defaults (only if value is None after normalization or missing for insert)
        numeric_applied = {
            k: v for k, v in numeric_defaults.items()
            if (is_insert and (k not in data or data.get(k) is None)) or (not is_insert and k in data and data.get(k) is None)
        }
        data.update(numeric_applied)
        
        # Handle item_id_in_data_source separately: only set to 0 if it's not in data or is None
        if "item_id_in_data_source" not in data or data.get("item_id_in_data_source") is None:
            data["item_id_in_data_source"] = 0
        
        # Datetime field defaults
        datetime_fields = {
            "start_date", "end_date", "inquiry_date", "cargo_readiness_date", "moved_time", "last_activity_time",
            "production_date", "loading_date", "etd", "eta", "latest_date_of_shipment",
            "lc_expiry_date", "shipping_date", "next_lots_loading_dates", "last_communication_time", "last_contact"
        }
        
        # Normalize empty strings to None for datetime fields (MySQL doesn't accept empty strings for datetime)
        for field in datetime_fields:
            if field in data:
                value = data.get(field)
                if value == "" or value == "0000-00-00 00:00:00" or (isinstance(value, str) and value.strip() == ""):
                    data[field] = None
        
        datetime_defaults = {
            field: datetime.now() for field in datetime_fields
            if (is_insert or field in data) and data.get(field) is None
        }
        data.update(datetime_defaults)
        
        # String field defaults
        string_fields = {
            "shipment_tracking", "lead", "comment", "additional_information", "pipeline",
            "stage_group", "repeat_inquiry", "source_information", "external_source",
            "ad_system", "medium", "ad_campaign_utm", "campaign_contents",
            "campaign_search_term", "purchase_order", "forwarder",
            "issuing_bank_ref_number", "advising_bank_ref_number", "ops",
            "buying_company", "client_payment_term", "incoterm", "bl_no",
            "doc_to_client_track_id", "container_number", "country_of_destination",
            "client_reference_number", "manufacturer_delivery_terms",
            "manufacture_payment_term", "pi_number", "export_company",
            "port_of_loading", "port_of_discharge", "postscript",
            "advising_bank", "confirming_bank", "issuing_bank", "ref_code",
            "shipping_line", "lost_reason", "sample_status", "buyer_type",
            "country", "urgency_level", "client_size", "manufacturer_payment_term",
            "email", "phone", "location", "website", "bitrix_url", "description"
        }
        string_defaults = {
            field: "" for field in string_fields
            if (is_insert or field in data) and data.get(field) is None
        }
        data.update(string_defaults)
        
        # Boolean field defaults
        if (is_insert or "eta_required_by_client" in data) and data.get("eta_required_by_client") is None:
            data["eta_required_by_client"] = False
        
        # JSON field defaults (fields that cannot be null and have default=list in model)
        json_fields_with_default = {
            "key_instructions_to_ops", "manufacturer", "hashtag", 
            "shipping_documents", "product_category", "observer_bitrixids", "observer_ids"
        }
        json_defaults = {
            field: [] for field in json_fields_with_default
            if (is_insert or field in data) and data.get(field) is None
        }
        data.update(json_defaults)
        
        return data

    @staticmethod
    async def create_request_activity_log(
        db: AsyncSession,
        request_id: int,
        action: Action,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create an activity log entry for a request operation.
        
        Args:
            db: Database session
            request_id: ID of the request
            action: Action type (CREATE, UPDATE, DELETE)
            user_id: Optional user ID who performed the action
            description: Optional description of the activity
            metadata: Optional metadata to store in activity_metadata
        """
        try:
            module_id = await BitrixWebhookMethods.get_module_id_for_requests(db)
            
            if not module_id:
                logger.warning("Request module not found in modules table, skipping activity log creation")
                return
            
            activity_log = ActivityLog(
                user_id=user_id,
                module_id=module_id,
                action=action,
                entity_id=str(request_id),
                description=description or f"Request {action.value}",
                activity_metadata=metadata
            )
            
            db.add(activity_log)
            await db.flush()
            
            logger.info(f"Created activity log for request {request_id} (action: {action.value})")
            
        except Exception as e:
            logger.error(f"Error creating activity log for request {request_id}: {e}", exc_info=True)
            logger.warning(f"Continuing without activity log for request {request_id}")

    @staticmethod
    async def create_request_stage_activities(
        db: AsyncSession,
        request_id: int,
        deal_stage: Optional[str] = None,
        phase: Optional[str] = None,
        current_stage_id: Optional[int] = None
    ) -> None:
        """
        Create RequestStageActivity records for a request based on deal_stage.
        
        Args:
            db: Database session
            request_id: ID of the request
            deal_stage: Deal stage string (e.g., "C24:NEW")
            phase: Request phase (e.g., "LEAD", "DEAL", "INQUIRY")
            current_stage_id: Current stage ID if already known
        """
        try:
            # If current_stage_id is provided, use it directly
            if current_stage_id:
                stage_id = current_stage_id
            elif deal_stage:
                # Parse deal_stage (format: "C24:NEW" or similar)
                # Extract stage name from deal_stage
                stage_name = deal_stage.split(":")[-1] if ":" in deal_stage else deal_stage
                
                # Try to find stage by name and parent_id (request_id)
                stmt = select(Stage.id).where(
                    Stage.stage_name == stage_name,
                    Stage.parent_id == request_id,
                    Stage.is_active == True
                ).limit(1)
                result = await db.execute(stmt)
                stage_id = result.scalar_one_or_none()
                
                # If not found, try to find a global stage (without parent_id)
                if not stage_id:
                    stmt = select(Stage.id).where(
                        Stage.stage_name == stage_name,
                        Stage.parent_id.is_(None),
                        Stage.is_active == True
                    ).limit(1)
                    result = await db.execute(stmt)
                    stage_id = result.scalar_one_or_none()
                
                # If still not found, create a new stage for this request
                if not stage_id:
                    from apps.v1.api.request.models.attribute import RequestPhase, StageStatus, RequestStatus
                    
                    # Determine phase from deal_stage or use provided phase
                    request_phase = RequestPhase.LEAD
                    if phase:
                        try:
                            request_phase = RequestPhase[phase.upper()]
                        except (KeyError, AttributeError):
                            pass
                    elif "DEAL" in deal_stage.upper() or "WON" in deal_stage.upper():
                        request_phase = RequestPhase.DEAL
                    elif "LOST" in deal_stage.upper():
                        request_phase = RequestPhase.DEAL
                    
                    new_stage = Stage(
                        parent_id=request_id,
                        stage_name=stage_name,
                        stage_status=StageStatus.NEW_UNCLEAR,
                        phase=request_phase,
                        status=RequestStatus.PENDING,
                        order_sequence=0,
                        is_active=True
                    )
                    db.add(new_stage)
                    await db.flush()
                    stage_id = new_stage.id
                    logger.info(f"Created new stage '{stage_name}' (ID: {stage_id}) for request {request_id}")
            else:
                # No deal_stage or current_stage_id provided, skip
                logger.warning(f"No deal_stage or current_stage_id provided for request {request_id}, skipping stage activity creation")
                return
            
            if not stage_id:
                logger.warning(f"Could not find or create stage for request {request_id} with deal_stage: {deal_stage}")
                return
            
            # Check if RequestStageActivity already exists for this request and stage
            check_stmt = select(RequestStageActivity.id).where(
                RequestStageActivity.request_id == request_id,
                RequestStageActivity.stage_id == stage_id
            ).limit(1)
            check_result = await db.execute(check_stmt)
            existing_activity = check_result.scalar_one_or_none()
            
            if existing_activity:
                logger.info(f"RequestStageActivity already exists for request {request_id} and stage {stage_id}")
                return
            
            # Get stage details for activity
            stage_stmt = select(Stage).where(Stage.id == stage_id).limit(1)
            stage_result = await db.execute(stage_stmt)
            stage = stage_result.scalar_one_or_none()
            
            if not stage:
                logger.warning(f"Stage {stage_id} not found, cannot create RequestStageActivity")
                return
            
            # Create RequestStageActivity
            from apps.v1.api.request.models.attribute import RequestPhase, RequestStatus
            
            activity_name = stage.stage_name or deal_stage or "New Activity"
            activity_phase = stage.phase if stage.phase else (RequestPhase.LEAD if not phase else RequestPhase[phase.upper()] if phase else RequestPhase.LEAD)
            
            new_activity = RequestStageActivity(
                request_id=request_id,
                stage_id=stage_id,
                activity_name=activity_name,
                activity_type="stage_transition",
                status=RequestStatus.PENDING,
                phase=activity_phase,
                order_sequence=stage.order_sequence or 0,
                is_completed=False
            )
            
            db.add(new_activity)
            await db.flush()
            
            logger.info(f"Created RequestStageActivity (ID: {new_activity.id}) for request {request_id} with stage {stage_id} ({activity_name})")
            
        except Exception as e:
            logger.error(f"Error creating RequestStageActivity for request {request_id}: {e}", exc_info=True)
            logger.warning(f"Continuing without RequestStageActivity for request {request_id}")
