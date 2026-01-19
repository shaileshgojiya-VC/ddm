"""
Bitrix webhook service to handle webhook notifications.
Returns simplified response with id, eventtype, and table for AI processing.
"""

import asyncio
import importlib.util
import json
import logging
import os
from typing import Any, Dict

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.bitrix.schema import BitrixWebhookRequest
from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService
from apps.monitor.process_product import process_product_data
from apps.monitor.process_company_1 import process_company_data
from apps.monitor.process_category import process_category_data

# Import process_deal_data from file with space in name
# Navigate from apps/v1/api/bitrix/services/ to apps/monitor/
# __file__ is at: apps/v1/api/bitrix/services/bitrix_webhook_service.py
# We need to go up 5 levels: services -> bitrix -> api -> v1 -> apps -> monitor
# 1: apps/v1/api/bitrix/services/
# 2: apps/v1/api/bitrix/
# 3: apps/v1/api/
# 4: apps/v1/
# 5: apps/
_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
_deal_module_path = os.path.join(_base_dir, "monitor", "process_deal 1.py")
_deal_spec = importlib.util.spec_from_file_location("process_deal_1", _deal_module_path)
_process_deal_module = importlib.util.module_from_spec(_deal_spec)
_deal_spec.loader.exec_module(_process_deal_module)
process_deal_data = _process_deal_module.process_deal_data

# Import process_user_data
_user_module_path = os.path.join(_base_dir, "monitor", "process_user.py")
_user_spec = importlib.util.spec_from_file_location("process_user", _user_module_path)
_process_user_module = importlib.util.module_from_spec(_user_spec)
_user_spec.loader.exec_module(_process_user_module)
process_user_data = _process_user_module.process_user_data

# Import process_contact_data
_contact_module_path = os.path.join(_base_dir, "monitor", "process_contact.py")
_contact_spec = importlib.util.spec_from_file_location("process_contact", _contact_module_path)
_process_contact_module = importlib.util.module_from_spec(_contact_spec)
_contact_spec.loader.exec_module(_process_contact_module)
process_contact_data = _process_contact_module.process_contact_data
from core.utils import constant_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class BitrixWebhookService:
    """Service to handle webhook notifications from Bitrix24. Returns simplified response for AI processing."""

    def __init__(self):
        """Initialize Bitrix webhook service."""
        logger.debug("BitrixWebhookService initialized for simplified webhook processing")

    def _is_document_webhook(self, webhook_data: BitrixWebhookRequest) -> bool:
        """
        Check if webhook data indicates a document event.
        Bitrix24 sometimes sends document updates as company events.
        """
        data = webhook_data.data

        # Check if data contains document-related fields
        if isinstance(data, dict):
            fields = data.get("FIELDS") or data
            if isinstance(fields, dict):
                # Check for document-specific fields
                if (
                    "FILE_ID" in fields
                    or "STORAGE_TYPE_ID" in fields
                    or "STORAGE_ELEMENT_ID" in fields
                ):
                    return True
                # Check if entity type is document
                if fields.get("ENTITY_TYPE_ID") == "8":  # Document entity type ID in Bitrix
                    return True

        # Check event name for document indicators
        event_upper = webhook_data.event.upper()
        if "FILE" in event_upper or "STORAGE" in event_upper:
            return True

        return False

    def _is_category_webhook(self, webhook_data: BitrixWebhookRequest) -> bool:
        """
        Check if webhook data indicates a category/section event.
        Bitrix24 sometimes sends category updates with product event names.
        """
        data = webhook_data.data

        # Check if data contains category/section-related fields
        if isinstance(data, dict):
            fields = data.get("FIELDS") or data
            if isinstance(fields, dict):
                # Check for category/section-specific fields
                # IBLOCK_SECTION_ID indicates it's a section/category
                if "IBLOCK_SECTION_ID" in fields:
                    return True
                # SECTION_ID indicates it's a section/category
                if "SECTION_ID" in fields:
                    return True
                # If IBLOCK_ID is present and it's a catalog section (not a product)
                # Products typically have more fields like PRICE, CURRENCY_ID, etc.
                if "IBLOCK_ID" in fields:
                    # If it lacks product-specific fields, it might be a section
                    has_product_fields = any(
                        key in fields
                        for key in ["PRICE", "CURRENCY_ID", "MEASURE", "VAT_ID", "VAT_INCLUDED"]
                    )
                    # If IBLOCK_ID is present but no product fields, likely a section
                    if not has_product_fields:
                        # Additional check: if NAME exists but no product-specific data, likely section
                        if "NAME" in fields and not any(
                            key in fields for key in ["PRICE", "CURRENCY_ID"]
                        ):
                            return True

        return False

    def _extract_id_from_webhook(self, webhook_data: BitrixWebhookRequest) -> str | None:
        """Extract ID from webhook data for any entity type."""
        data = webhook_data.data

        # If data is a dict, check for FIELDS or direct ID
        if isinstance(data, dict):
            fields = data.get("FIELDS") or data
            if isinstance(fields, dict):
                return str(fields.get("ID") or fields.get("id") or fields.get("Id") or "")

        # If data is a list, get first item
        elif isinstance(data, list) and data:
            item = data[0]
            if isinstance(item, dict):
                return str(item.get("ID") or item.get("id") or item.get("Id") or "")

        # If data is a JSON string, parse it
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

    def _determine_event_type(self, event_name: str) -> str:
        """Determine event type: INSERT, UPDATE, or DELETE."""
        event_upper = event_name.upper()
        if "DELETE" in event_upper:
            return "DELETE"
        elif "ADD" in event_upper or "CREATE" in event_upper:
            return "INSERT"
        elif "UPDATE" in event_upper:
            return "UPDATE"
        return "UNKNOWN"

    def _determine_table_type(self, event_name: str) -> str:
        """
        Determine table type from webhook event name.

        Supported table types:
        - product: Product-related events (ONCRMPRODUCT*)
        - category: Category/Section-related events (ONCRMPRODUCTSECTION*, ONIBLOCKSECTION*)
        - product_section: Product section events (alternative name)
        - company: Company/Supplier-related events (ONCRMCOMPANY*)
        - deal: Deal/Request-related events (ONCRMDEAL*)
        - registration: Registration-related events
        - contact: Contact-related events (ONCRMCONTACT*)
        - customer: Customer-related events (ONCRMCUSTOMER*)
        - document: Document-related events (ONCRMDOCUMENT*)
        - user: User-related events (ONUSERADD - only INSERT for new users)

        Bitrix24 event naming patterns:
        - ONCRMPRODUCTADD, ONCRMPRODUCTUPDATE, ONCRMPRODUCTDELETE
        - ONCRMPRODUCTSECTIONADD, ONCRMPRODUCTSECTIONUPDATE, ONCRMPRODUCTSECTIONDELETE
        - ONIBLOCKSECTIONADD, ONIBLOCKSECTIONUPDATE, ONIBLOCKSECTIONDELETE
        - ONCRMCOMPANYADD, ONCRMCOMPANYUPDATE, ONCRMCOMPANYDELETE
        - ONCRMDEALADD, ONCRMDEALUPDATE, ONCRMDEALDELETE
        - ONCRMCONTACTADD, ONCRMCONTACTUPDATE, ONCRMCONTACTDELETE
        - ONCRMDOCUMENTADD, ONCRMDOCUMENTUPDATE, ONCRMDOCUMENTDELETE
        - ONUSERADD (only INSERT events for new users)
        """
        event_upper = event_name.upper()
        logger.debug(f"🔍 Determining table type from event: {event_name} (upper: {event_upper})")

        # Check for more specific patterns first (category/section before everything else to avoid false matches)
        # IMPORTANT: Check for SECTION/CATEGORY before DOCUMENT and PRODUCT to prevent misclassification
        # Check for explicit section events first (must contain "SECTION" in the event name)
        has_section = "PRODUCTSECTION" in event_upper
        if has_section:
            # Explicit product section or info block section events
            table_type = "category"
            logger.info(
                f"📁 Category/Section event detected (explicit): {event_name} → table: {table_type}"
            )
        elif "DOCUMENT" in event_upper:
            # Document events (only if not a section event)
            table_type = "document"
            logger.info(f"📄 Document event detected: {event_name} → table: {table_type}")
        elif "USER" in event_upper:
            table_type = "user"
            logger.info(f"👤 User event detected: {event_name} → table: {table_type}")
        elif "PRODUCT" in event_upper:
            # Product events (ONCRMPRODUCT* but NOT ONCRMPRODUCTSECTION*)
            table_type = "product"
            logger.info(f"📦 Product event detected: {event_name} → table: {table_type}")
        elif "COMPANY" in event_upper:
            table_type = "company"  # supplier
        elif "DEAL" in event_upper:
            table_type = "deal"  # request
        elif "REGISTRATION" in event_upper:
            table_type = "registration"
        elif "CONTACT" in event_upper:
            table_type = "contact"
        elif "CUSTOMER" in event_upper:
            table_type = "customer"
        else:
            table_type = "unknown"
            logger.warning(f"⚠️ Unknown event type: {event_name}. Could not determine table type.")

        logger.debug(f"✅ Determined table type: {table_type} for event: {event_name}")
        return table_type

    async def _call_ai_function(
        self, 
        db: AsyncSession,
        webhook_data: Dict[str, Any]
    ) -> None:
        """
        Call AI function with webhook data.

        This function will be called with the extracted webhook data:
        {
            "id": str,           # Entity ID from Bitrix
            "eventtype": str,    # INSERT, UPDATE, or DELETE
            "table": str         # product, category, product_section, company, deal, registration, contact, customer, document, or user
        }

        TODO: Implement AI function call logic here.
        Examples:
        - Call external AI API
        - Process with AutoGen
        - Send to QDrant for vector search
        - Use Streamlit for AI processing
        """
        try:
            logger.info("🤖 Calling AI function with webhook data...")

            # Extract data for AI processing
            entity_id = webhook_data.get("id")
            event_type = webhook_data.get("eventtype")
            table_type = webhook_data.get("table")

            # Log AI function call
            logger.info(f"   AI Function Input:")
            logger.info(f"   - Entity ID: {entity_id}")
            logger.info(f"   - Event Type: {event_type}")
            logger.info(f"   - Table Type: {table_type}")

            # Call AI function based on table type
            if table_type == "product":
                # Call process_product_data function for product processing
                logger.info(f"📦 Processing product data for ID: {entity_id}")
                try:
                    input_data = {
                        "id": entity_id,
                        "eventtype": event_type,
                        "table": table_type
                    }
                    
                    # Call the AI function (synchronous function in async context)
                    # Run in executor to avoid blocking the event loop
                    output_data = await asyncio.to_thread(process_product_data, input_data)
                    
                    # Log the output in JSON format for AI processing
                    logger.info("=" * 80)
                    logger.info("🤖 AI FUNCTION OUTPUT (JSON FORMAT FOR AI PROCESSING):")
                    logger.info("=" * 80)
                    output_json = json.dumps(
                        output_data,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(output_json)
                    logger.info("=" * 80)
                    
                    # Transform AI output and pass to /data API via WebhookDataService
                    logger.info("🔄 Transforming AI output and passing to /data API...")
                    
                    # Extract data from AI output
                    product_data = output_data.get("product", {}).copy()
                    mapping_data = output_data.get("mapping", {})
                    logistic_data = output_data.get("logistic", {})
                    
                    # Convert mapping to list format for bridge tables
                    mapping_list = []
                    
                    # Handle product_suppliers mapping
                    if mapping_data.get("product_id") and mapping_data.get("supplier_id"):
                        product_ids = mapping_data.get("product_id", [])
                        supplier_ids = mapping_data.get("supplier_id", [])
                        if product_ids and supplier_ids:
                            mapping_list.append({
                                "table": "product_suppliers",
                                "data": {
                                    "product_id": product_ids[0] if product_ids else None,
                                    "supplier_id": supplier_ids[0] if supplier_ids else None,
                                }
                            })
                    
                    # Handle logistic data - add as separate mapping entry for logistic table
                    # Logistic table has: cartons_per_pallet, loading_quantities, transport_delivery_conditions_temperature,
                    # storage_conditions_temperature, carton_dimensions, pallet_dimensions, term_of_delivery, product_id
                    # Note: Some logistic fields (loading_address, lead_time_*, moq_*) are in products table
                    # Note: product_id will be set to the database ID (record_id) in _handle_mapping, not Bitrix ID
                    if logistic_data:
                        # Prepare logistic mapping data (only fields that belong to logistic table)
                        # Do NOT include product_id here - it will be set to the database record_id in _handle_mapping
                        logistic_mapping_data = {
                            "cartons_per_pallet": logistic_data.get("cartons_per_pallet"),
                            "loading_quantities": logistic_data.get("loading_quantities"),
                            "transport_delivery_conditions_temperature": logistic_data.get("transport_delivery_conditions_temperature"),
                            "storage_conditions_temperature": logistic_data.get("storage_conditions_temperature"),
                            "carton_dimensions": logistic_data.get("carton_dimensions"),
                            "pallet_dimensions": logistic_data.get("pallet_dimensions"),
                            "term_of_delivery": logistic_data.get("term_of_delivery"),
                        }
                        
                        # Add logistic mapping to mapping_list (product_id will be set from record_id in _handle_mapping)
                        mapping_list.append({
                            "table": "logistic",
                            "data": logistic_mapping_data
                        })
                        
                        # Merge product-specific logistic fields into product_data
                        # These fields belong to products table, not logistic table
                        product_logistic_fields = {
                            "loading_address": logistic_data.get("loading_address"),
                            "lead_time_to_print_packing_material": logistic_data.get("lead_time_to_print_packing_material"),
                            "lead_time_to_reorder_packing_material": logistic_data.get("lead_time_to_reorder_packing_material"),
                            "moq_packaging_matereal": logistic_data.get("moq_packaging_matereal"),
                            "moq_production": logistic_data.get("moq_production"),
                        }
                        # Only add non-None values
                        for key, value in product_logistic_fields.items():
                            if value is not None:
                                product_data[key] = value
                    
                    # Prepare data for WebhookDataService
                    webhook_service = WebhookDataService()
                    service_result = await webhook_service.process_webhook_data(
                        db=db,
                        eventtype=event_type.lower(),  # Convert to lowercase (insert/update/delete)
                        table=table_type.lower(),
                        data=product_data,
                        bitrix_id=entity_id,
                        mapping=mapping_list if mapping_list else None,
                        webhook="bitrix"
                    )
                    
                    logger.info("=" * 80)
                    logger.info("✅ DATA API RESPONSE (from WebhookDataService):")
                    logger.info("=" * 80)
                    service_result_json = json.dumps(
                        service_result,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(service_result_json)
                    logger.info("=" * 80)
                    
                    logger.info(f"✅ Product data processed and saved successfully for ID: {entity_id}")
                except Exception as product_error:
                    logger.error(f"❌ Error processing product data for ID {entity_id}: {product_error}", exc_info=True)
                    raise
            elif table_type == "company":
                # Call process_company_data function for company/supplier/customer processing
                logger.info(f"🏢 Processing company data for ID: {entity_id}")
                try:
                    input_data = {
                        "id": entity_id,
                        "eventtype": event_type,
                        "table": table_type
                    }
                    
                    # Call the AI function (synchronous function in async context)
                    # Run in executor to avoid blocking the event loop
                    output_data = await asyncio.to_thread(process_company_data, input_data)
                    
                    # Log the output in JSON format for AI processing
                    logger.info("=" * 80)
                    logger.info("🤖 AI FUNCTION OUTPUT (JSON FORMAT FOR AI PROCESSING):")
                    logger.info("=" * 80)
                    output_json = json.dumps(
                        output_data,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(output_json)
                    logger.info("=" * 80)
                    
                    # Transform AI output and pass to /data API via WebhookDataService
                    logger.info("🔄 Transforming AI output and passing to /data API...")
                    
                    # Extract company data from AI output
                    # The output_data IS the company data (not nested like products)
                    company_data = output_data.copy()
                    
                    # Determine target table based on COMPANY_TYPE
                    company_type = company_data.get("Company_type") or company_data.get("COMPANY_TYPE") or company_data.get("company_type", "").lower()
                    
                    # Remove metadata fields that shouldn't be saved to database
                    company_data.pop("eventtype", None)
                    company_data.pop("table", None)
                    company_data.pop("webhook", None)
                    
                    # Determine target table and prepare mapping data
                    target_table = "suppliers"  # Default to suppliers (plural - matches actual table name)
                    mapping_list = []
                    
                    # Check COMPANY_TYPE to determine if it's a customer or supplier
                    if company_type:
                        company_type_lower = str(company_type).lower()
                        if "customer" in company_type_lower or "buyer" in company_type_lower:
                            target_table = "customers"  # Use plural to match actual table name
                            logger.info(f"📋 Company type '{company_type}' detected - routing to CUSTOMERS table")
                        else:
                            target_table = "suppliers"  # Use plural to match actual table name
                            logger.info(f"🏭 Company type '{company_type}' detected - routing to SUPPLIERS table")
                    else:
                        logger.warning(f"⚠️ COMPANY_TYPE not found in data, defaulting to SUPPLIERS table")
                    
                    # Extract bridge table mappings based on target table
                    if target_table == "suppliers":
                        # Supplier bridge tables: product_suppliers, supplier_emails, documents, requests
                        if "product_suppliers" in company_data:
                            product_suppliers = company_data.pop("product_suppliers", [])
                            if product_suppliers and isinstance(product_suppliers, list):
                                for ps_mapping in product_suppliers:
                                    if isinstance(ps_mapping, dict) and "product_id" in ps_mapping:
                                        mapping_list.append({
                                            "table": "product_suppliers",
                                            "data": {
                                                "product_id": ps_mapping.get("product_id"),
                                                "name": ps_mapping.get("name")
                                                # supplier_id will be set to record_id in _handle_mapping
                                            }
                                        })
                        
                        # Note: supplier_emails, documents, and requests mappings can be added here if needed
                        # For now, we'll handle product_suppliers as the main mapping
                    elif target_table == "customer":
                        # Customer bridge tables: request_customers
                        if "request_customers" in company_data:
                            request_customers = company_data.pop("request_customers", [])
                            if request_customers and isinstance(request_customers, list):
                                for rc_mapping in request_customers:
                                    if isinstance(rc_mapping, dict) and "request_id" in rc_mapping:
                                        mapping_list.append({
                                            "table": "request_customers",
                                            "data": {
                                                "request_id": rc_mapping.get("request_id")
                                                # customer_id will be set to record_id in _handle_mapping
                                            }
                                        })
                    
                    # Prepare data for WebhookDataService
                    webhook_service = WebhookDataService()
                    service_result = await webhook_service.process_webhook_data(
                        db=db,
                        eventtype=event_type.lower(),  # Convert to lowercase (insert/update/delete)
                        table=target_table.lower(),  # Use determined target table
                        data=company_data,
                        bitrix_id=entity_id,
                        mapping=mapping_list if mapping_list else None,
                        webhook="bitrix"
                    )
                    
                    logger.info("=" * 80)
                    logger.info("✅ DATA API RESPONSE (from WebhookDataService):")
                    logger.info("=" * 80)
                    service_result_json = json.dumps(
                        service_result,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(service_result_json)
                    logger.info("=" * 80)
                    
                    logger.info(f"✅ Company data processed and saved successfully for ID: {entity_id} (table: {target_table})")
                except Exception as company_error:
                    logger.error(f"❌ Error processing company data for ID {entity_id}: {company_error}", exc_info=True)
                    raise
            elif table_type == "deal":
                # Call process_deal_data function for deal/request processing
                logger.info(f"💼 Processing deal/request data for ID: {entity_id}")
                try:
                    input_data = {
                        "id": entity_id,
                        "eventtype": event_type,
                        "table": table_type
                    }
                    
                    # Call the AI function (synchronous function in async context)
                    # Run in executor to avoid blocking the event loop
                    output_data = await asyncio.to_thread(process_deal_data, input_data)
                    
                    # Log the output in JSON format for AI processing
                    logger.info("=" * 80)
                    logger.info("🤖 AI FUNCTION OUTPUT (JSON FORMAT FOR AI PROCESSING):")
                    logger.info("=" * 80)
                    output_json = json.dumps(
                        output_data,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(output_json)
                    logger.info("=" * 80)
                    
                    # Transform AI output and pass to /data API via WebhookDataService
                    logger.info("🔄 Transforming AI output and passing to /data API...")
                    
                    # Extract deal data from AI output
                    # The output_data has structure: { "deal": {...}, "mapping": {...} }
                    deal_data = output_data.get("deal", {}).copy()
                    mapping_data = output_data.get("mapping", {})
                    
                    # Remove metadata fields that shouldn't be saved to database
                    deal_data.pop("eventtype", None)
                    deal_data.pop("table", None)
                    deal_data.pop("webhook", None)
                    
                    # Prepare mapping list for bridge tables
                    mapping_list = []
                    
                    # Extract product_ids from mapping and create request_products mappings
                    product_ids = mapping_data.get("product_id", [])
                    if product_ids and isinstance(product_ids, list):
                        for product_id in product_ids:
                            if product_id:
                                mapping_list.append({
                                    "table": "request_products",
                                    "data": {
                                        "product_id": product_id
                                        # request_id will be set to record_id in _handle_mapping
                                    }
                                })
                    
                    # Extract company_id and determine if it's a customer or supplier
                    company_id = mapping_data.get("company_id")
                    company_type = mapping_data.get("company_type", "").upper() if mapping_data.get("company_type") else ""
                    
                    # Also check if company_id is already in deal_data (from AI processing)
                    if not company_id and "company_id" in deal_data:
                        company_id = deal_data.get("company_id")
                    
                    # Handle company_id based on company_type
                    if company_id:
                        from sqlalchemy import select
                        from apps.v1.api.suppliers.models.model import Suppliers
                        
                        if "CUSTOMER" in company_type or "BUYER" in company_type:
                            # For customers, create request_customers mapping (don't set company_id in deal_data)
                            # Remove company_id from deal_data if it exists
                            deal_data.pop("company_id", None)
                            mapping_list.append({
                                "table": "request_customers",
                                "data": {
                                    "company_bitrix_id": company_id  # Will be resolved in _handle_mapping
                                    # request_id will be set to record_id in _handle_mapping
                                }
                            })
                            logger.info(f"📋 Company type '{company_type}' detected - will create request_customers mapping")
                        else:
                            # For suppliers, convert Bitrix company ID to database supplier ID
                            # company_id is a Bitrix ID, need to find database supplier ID
                            
                            # Try to find supplier by Bitrix ID
                            supplier_stmt = select(Suppliers.id).where(Suppliers.bitrix_id == str(company_id))
                            supplier_result = await db.execute(supplier_stmt)
                            db_supplier_id = supplier_result.scalar_one_or_none()
                            
                            if db_supplier_id:
                                # Set the database supplier ID in deal_data
                                deal_data["company_id"] = db_supplier_id
                                logger.info(f"🏭 Company type '{company_type}' detected - converted Bitrix company_id {company_id} to database supplier_id {db_supplier_id}")
                            else:
                                # Supplier not found - log warning and don't set company_id
                                logger.warning(f"⚠️ Supplier with Bitrix ID {company_id} not found in database. Skipping company_id in deal_data.")
                                # Remove company_id from deal_data if it exists
                                deal_data.pop("company_id", None)
                    else:
                        # No company_id in mapping or deal_data - remove if exists
                        deal_data.pop("company_id", None)
                    
                    # Prepare data for WebhookDataService
                    webhook_service = WebhookDataService()
                    service_result = await webhook_service.process_webhook_data(
                        db=db,
                        eventtype=event_type.lower(),  # Convert to lowercase (insert/update/delete)
                        table="request",  # Use "request" as table name (not "deal")
                        data=deal_data,
                        bitrix_id=entity_id,
                        mapping=mapping_list if mapping_list else None,
                        webhook="bitrix"
                    )
                    
                    logger.info("=" * 80)
                    logger.info("✅ DATA API RESPONSE (from WebhookDataService):")
                    logger.info("=" * 80)
                    service_result_json = json.dumps(
                        service_result,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(service_result_json)
                    logger.info("=" * 80)
                    
                    logger.info(f"✅ Deal/Request data processed and saved successfully for ID: {entity_id}")
                except Exception as deal_error:
                    logger.error(f"❌ Error processing deal/request data for ID {entity_id}: {deal_error}", exc_info=True)
                    raise
            elif table_type == "registration":
                # Handle registration AI processing
                logger.info(f"📝 Registration processing not yet implemented for ID: {entity_id}")
                pass
            elif table_type == "contact":
                # Handle contact AI processing
                logger.info(f"👤 Processing contact data for ID: {entity_id}")
                try:
                    input_data = {
                        "id": entity_id,
                        "eventtype": event_type,
                        "table": table_type
                    }
                    output_data = await asyncio.to_thread(process_contact_data, input_data)
                    logger.info("=" * 80)
                    logger.info("🤖 AI FUNCTION OUTPUT (JSON FORMAT FOR AI PROCESSING):")
                    logger.info("=" * 80)
                    output_json = json.dumps(
                        output_data,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(output_json)
                    logger.info("=" * 80)
                    
                    # Extract contact data from AI output
                    contact_data = output_data.copy()
                    
                    # Determine target table based on company's COMPANY_TYPE
                    # Contacts are identified from the "company" field, and company_type determines routing
                    company_type = contact_data.get("company_type") or contact_data.get("Company_type") or contact_data.get("COMPANY_TYPE")
                    if company_type:
                        # Handle if it's a dict with ID or VALUE
                        if isinstance(company_type, dict):
                            company_type = company_type.get("ID") or company_type.get("VALUE") or str(company_type)
                        else:
                            company_type = str(company_type)
                    
                    # Remove metadata fields that shouldn't be saved to database
                    contact_data.pop("eventtype", None)
                    contact_data.pop("table", None)
                    contact_data.pop("webhook", None)
                    contact_data.pop("id", None)  # Remove id, use bitrix_id instead
                    contact_data.pop("company_type", None)  # Remove company_type, it's only used for routing
                    contact_data.pop("Company_type", None)
                    contact_data.pop("COMPANY_TYPE", None)
                    
                    # Map full_name to name for customers/suppliers table
                    if "full_name" in contact_data:
                        contact_data["name"] = contact_data.pop("full_name")
                    
                    # Determine target table based on company_type (same logic as companies)
                    target_table = "suppliers"  # Default to suppliers (plural - matches actual table name)
                    
                    # Check COMPANY_TYPE to determine if it's a customer or supplier
                    if company_type:
                        company_type_lower = str(company_type).lower()
                        if "customer" in company_type_lower or "buyer" in company_type_lower:
                            target_table = "customers"  # Use plural to match actual table name
                            logger.info(f"📋 Contact's company type '{company_type}' detected - routing to CUSTOMERS table")
                        else:
                            target_table = "suppliers"  # Use plural to match actual table name
                            logger.info(f"🏭 Contact's company type '{company_type}' detected - routing to SUPPLIERS table")
                    else:
                        logger.warning(f"⚠️ COMPANY_TYPE not found in contact data, defaulting to SUPPLIERS table")
                    
                    # Prepare data for WebhookDataService
                    webhook_service = WebhookDataService()
                    service_result = await webhook_service.process_webhook_data(
                        db=db,
                        eventtype=event_type.lower(),
                        table=target_table,  # Route based on company_type
                        data=contact_data,
                        bitrix_id=entity_id,
                        mapping=None,  # Contacts don't have bridge tables
                        webhook="bitrix"
                    )
                    
                    logger.info("=" * 80)
                    logger.info("✅ DATA API RESPONSE (from WebhookDataService):")
                    logger.info("=" * 80)
                    service_result_json = json.dumps(
                        service_result,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(service_result_json)
                    logger.info("=" * 80)
                    
                    logger.info(f"✅ Contact data processed and saved successfully for ID: {entity_id}")
                except Exception as contact_error:
                    logger.error(f"❌ Error processing contact data for ID {entity_id}: {contact_error}", exc_info=True)
                    raise
            elif table_type == "customer":
                # Handle customer AI processing
                logger.info(f"👥 Customer processing not yet implemented for ID: {entity_id}")
                pass
            elif table_type == "document":
                # Handle document AI processing
                logger.info(f"📄 Document processing not yet implemented for ID: {entity_id}")
                pass
            elif table_type == "category":
                # Call process_category_data function for category processing
                logger.info(f"📁 Processing category data for ID: {entity_id}")
                try:
                    input_data = {
                        "id": entity_id,
                        "eventtype": event_type,
                        "table": table_type
                    }
                    
                    # Call the AI function (synchronous function in async context)
                    # Run in executor to avoid blocking the event loop
                    output_data = await asyncio.to_thread(process_category_data, input_data)
                    
                    # Log the output in JSON format for AI processing
                    logger.info("=" * 80)
                    logger.info("🤖 AI FUNCTION OUTPUT (JSON FORMAT FOR AI PROCESSING):")
                    logger.info("=" * 80)
                    output_json = json.dumps(
                        output_data,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(output_json)
                    logger.info("=" * 80)
                    
                    # Transform AI output and pass to /data API via WebhookDataService
                    logger.info("🔄 Transforming AI output and passing to /data API...")
                    
                    # Extract category data from AI output
                    # The output_data IS the category data (not nested like products)
                    category_data = output_data.copy()
                    
                    # Remove metadata fields that shouldn't be saved to database
                    category_data.pop("eventtype", None)
                    category_data.pop("table", None)
                    category_data.pop("webhook", None)
                    
                    # Map field names from process_category output to database column names
                    # process_category returns: bitrix_id, catelog_id, section_id, name, code, external_id
                    # Database expects: bitrix_id, catelog_id, section_id, name, code, external_id
                    # The field mapping is already done in process_category.py, so we can use it directly
                    
                    # Prepare data for WebhookDataService
                    webhook_service = WebhookDataService()
                    service_result = await webhook_service.process_webhook_data(
                        db=db,
                        eventtype=event_type.lower(),  # Convert to lowercase (insert/update/delete)
                        table=table_type.lower(),
                        data=category_data,
                        bitrix_id=entity_id,
                        mapping=None,  # Categories don't have bridge tables
                        webhook="bitrix"
                    )
                    
                    logger.info("=" * 80)
                    logger.info("✅ DATA API RESPONSE (from WebhookDataService):")
                    logger.info("=" * 80)
                    service_result_json = json.dumps(
                        service_result,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(service_result_json)
                    logger.info("=" * 80)
                    
                    logger.info(f"✅ Category data processed and saved successfully for ID: {entity_id}")
                except Exception as category_error:
                    logger.error(f"❌ Error processing category data for ID {entity_id}: {category_error}", exc_info=True)
                    raise
                logger.info(f"📁 Category/Section processing not yet implemented for ID: {entity_id}")
                pass
            elif table_type == "product_section":
                # Handle product section AI processing (alternative name)
                logger.info(f"📁 Product Section processing not yet implemented for ID: {entity_id}")
                pass
            elif table_type == "user":
                # Handle user AI processing (only INSERT events)
                logger.info(f"👤 Processing user data for ID: {entity_id}")
                try:
                    input_data = {
                        "id": entity_id,
                        "eventtype": event_type,
                        "table": table_type
                    }
                    output_data = await asyncio.to_thread(process_user_data, input_data)
                    logger.info("=" * 80)
                    logger.info("🤖 AI FUNCTION OUTPUT (JSON FORMAT FOR AI PROCESSING):")
                    logger.info("=" * 80)
                    output_json = json.dumps(
                        output_data,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(output_json)
                    logger.info("=" * 80)
                    
                    # Extract user data from AI output
                    user_data = output_data.copy()
                    
                    # Remove metadata fields that shouldn't be saved to database
                    user_data.pop("eventtype", None)
                    user_data.pop("table", None)
                    user_data.pop("webhook", None)
                    
                    # Prepare data for WebhookDataService
                    webhook_service = WebhookDataService()
                    service_result = await webhook_service.process_webhook_data(
                        db=db,
                        eventtype=event_type.lower(),
                        table="user",
                        data=user_data,
                        bitrix_id=entity_id,
                        mapping=None,  # Users don't have bridge tables
                        webhook="bitrix"
                    )
                    
                    logger.info("=" * 80)
                    logger.info("✅ DATA API RESPONSE (from WebhookDataService):")
                    logger.info("=" * 80)
                    service_result_json = json.dumps(
                        service_result,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )
                    logger.info(service_result_json)
                    logger.info("=" * 80)
                    
                    logger.info(f"✅ User data processed and saved successfully for ID: {entity_id}")
                except Exception as user_error:
                    logger.error(f"❌ Error processing user data for ID {entity_id}: {user_error}", exc_info=True)
                    raise
            else:
                logger.warning(f"⚠️ Unknown table type: {table_type}, skipping AI processing")

            logger.info("✅ AI function call completed")

        except Exception as exc:
            logger.error(f"❌ Error in AI function call: {exc}", exc_info=True)
            raise

    async def process_webhook(
        self,
        db: AsyncSession,
        webhook_data: BitrixWebhookRequest,
    ) -> Dict[str, Any]:
        """
        Process webhook notification and return simplified response.

        Returns:
            {
                "id": str,           # Entity ID from Bitrix
                "eventtype": str,    # INSERT, UPDATE, or DELETE
                "table": str,        # product, category, product_section, company, deal, registration, contact, customer, document, or user
                "webhook": str       # Always "bitrix" to indicate data is from webhook
            }
        """
        try:
            logger.info(f"🔔 Processing Bitrix webhook event: {webhook_data.event}")
            logger.info(f"📦 Webhook data type: {type(webhook_data.data)}")
            logger.info(
                f"📦 Webhook data content: {json.dumps(webhook_data.data, indent=2, default=str) if webhook_data.data else 'None'}"
            )

            # Extract ID from webhook
            entity_id = self._extract_id_from_webhook(webhook_data)
            if not entity_id:
                logger.error(f"❌ Missing ID in webhook data. Event: {webhook_data.event}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data={"webhook": "bitrix"},
                    message="Missing ID in webhook data",
                ).make

            # Determine event type and table type
            event_type = self._determine_event_type(webhook_data.event)
            table_type = self._determine_table_type(webhook_data.event)

            # For user webhooks: Only process INSERT events (new users), skip UPDATE and DELETE
            if table_type == "user":
                if event_type != "INSERT":
                    logger.info(
                        f"⏭️ Skipping user webhook: Only INSERT (new user) events are processed. Event type: {event_type}"
                    )
                    return StandardResponse(
                        status=constant_variable.STATUS_SUCCESS,
                        status_code=status.HTTP_200_OK,
                        data={
                            "id": entity_id,
                            "eventtype": event_type,
                            "table": table_type,
                            "webhook": "bitrix",
                            "skipped": True,
                            "reason": "User webhooks only process INSERT events (new users)",
                        },
                        message=f"User webhook received but skipped (only INSERT events processed): {event_type}",
                    ).make
                logger.info(f"✅ Processing user INSERT event (new user): ID={entity_id}")

            # Prepare simplified response
            response_data = {
                "id": entity_id,
                "eventtype": event_type,
                "table": table_type,
                "webhook": "bitrix",
            }

            # Log the response in JSON format
            response_json = json.dumps(response_data, indent=2, ensure_ascii=False)
            logger.info("=" * 80)
            logger.info("📋 WEBHOOK RESPONSE (for AI processing) - JSON FORMAT:")
            logger.info(response_json)
            logger.info("=" * 80)

            # For DELETE events: Skip AI function and directly perform soft delete
            if event_type == "DELETE":
                logger.info(f"🗑️ DELETE event detected - skipping AI function and performing direct soft delete")
                try:
                    webhook_data_service = WebhookDataService()
                    delete_result = await webhook_data_service.delete_record(
                        db=db,
                        table_name=table_type,
                        bitrix_id=entity_id
                    )
                    logger.info(f"✅ Successfully deleted record: {delete_result}")
                    return StandardResponse(
                        status=constant_variable.STATUS_SUCCESS,
                        status_code=status.HTTP_200_OK,
                        data={
                            **response_data,
                            "delete_result": delete_result
                        },
                        message=f"Record deleted: {table_type} (ID: {entity_id}, Type: {delete_result.get('delete_type', 'unknown')})",
                    ).make
                except Exception as delete_error:
                    logger.error(f"❌ Error during DELETE operation: {delete_error}", exc_info=True)
                    return StandardResponse(
                        status=constant_variable.STATUS_FAIL,
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        data=response_data,
                        message=f"Error deleting record: {str(delete_error)}",
                    ).make

            # Call AI function with the extracted data (for INSERT and UPDATE events only)
            try:
                await self._call_ai_function(db=db, webhook_data=response_data)
            except Exception as ai_error:
                logger.warning(f"⚠️ AI function call failed (non-critical): {ai_error}")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=response_data,
                message=f"Webhook processed: {table_type} {event_type} (ID: {entity_id})",
            ).make

        except Exception as exc:
            logger.error(f"❌ Error processing webhook: {exc}", exc_info=True)
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"webhook": "bitrix"},
                message=f"Error processing webhook: {str(exc)}",
            ).make
