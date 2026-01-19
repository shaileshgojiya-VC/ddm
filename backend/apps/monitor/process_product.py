#!/usr/bin/env python3
"""
Script to process product data:
1. Extract product ID from input
2. Call catalog.product.get to get dateActiveFrom and dateActiveTo
3. Add these dates to the product data
4. Map field names using the schema
5. Create supplier_product_mapping.json
"""

import json
import os
import re
import sys
import requests
from typing import Dict, Any, Optional

# Bitrix webhook URL - configured directly in this file
BITRIX_WEBHOOK_URL = "https://dana.bitrix24.eu/rest/218/8cxeo979k998jzqq/"


# Field mapping from schema (PROPERTY_* to readable names)
FIELD_MAPPING = {
    "ID": "ID",
    "CATALOG_ID": "CATALOG_ID",
    "PRICE": "PRICE",
    "CURRENCY_ID": "CURRENCY_ID",
    "NAME": "NAME",
    "CODE": "CODE",
    "DESCRIPTION": "DESCRIPTION",
    "DESCRIPTION_TYPE": "DESCRIPTION_TYPE",
    "ACTIVE": "ACTIVE",
    "SECTION_ID": "SECTION_ID",
    "SORT": "SORT",
    "VAT_ID": "VAT_ID",
    "VAT_INCLUDED": "VAT_INCLUDED",
    "MEASURE": "MEASURE",
    "XML_ID": "XML_ID",
    "PREVIEW_PICTURE": "PREVIEW_PICTURE",
    "DETAIL_PICTURE": "DETAIL_PICTURE",
    "DATE_CREATE": "DATE_CREATE",
    "TIMESTAMP_X": "TIMESTAMP_X",
    "MODIFIED_BY": "MODIFIED_BY",
    "CREATED_BY": "CREATED_BY",
    "PROPERTY_98": "Barcode",
    "PROPERTY_194": "Carton_Barcode",
    "PROPERTY_126": "Bestseller",
    "PROPERTY_128": "Special_Offer",
    "PROPERTY_248": "product",
    "PROPERTY_130": "Art_Number",
    "PROPERTY_92": "Factory_Logo",
    "PROPERTY_102": "specifications",
    "PROPERTY_104": "Product_Artwork",
    "PROPERTY_108": "Factory",
    "PROPERTY_110": "Country_of_Origin",
    "PROPERTY_112": "HS_Code",
    "PROPERTY_114": "Package_Material",
    "PROPERTY_118": "Net_Content",
    "PROPERTY_138": "Background_Image",
    "PROPERTY_160": "Shelf_Life",
    "PROPERTY_162": "Units_per_Carton",
    "PROPERTY_166": "Loading_Quantities",
    "PROPERTY_174": "Product_Category",
    "PROPERTY_184": "Product_Short_Name",
    "PROPERTY_186": "Link_to_Artwork_Files",
    "PROPERTY_190": "SKU_Package",
    "PROPERTY_192": "Cartons_per_Pallet",
    "PROPERTY_196": "Carton_Artwork",
    "PROPERTY_200": "Photo_Primary_Packing",
    "PROPERTY_202": "Photo_Secondary_Packing",
    "PROPERTY_204": "Technical_Data_Sheet",
    "PROPERTY_208": "Primary_Packing_Artwork",
    "PROPERTY_210": "Secondary_Packing_Artwork",
    "PROPERTY_216": "transport_conditions_temperature",
    "PROPERTY_218": "storage_conditions_temperature",
    "PROPERTY_220": "Carton_Dimensions",
    "PROPERTY_222": "Pallet_Dimensions",
    "PROPERTY_228": "Lead_Time_Print_Packing",
    "PROPERTY_230": "Lead_Time_Reorder_Packing",
    "PROPERTY_232": "Lead_Time_Production",
    "PROPERTY_234": "art_works_approved_by_fda_of_country_of_destination",
    "PROPERTY_242": "Loading_Address",
    "PROPERTY_244": "Unit_Pack_Size",
    "PROPERTY_250": "Packing",
    "PROPERTY_252": "Carton",
    "PROPERTY_254": "Term_of_Delivery",
    "PROPERTY_256": "Price",
    "PROPERTY_258": "Quantity",
    "PROPERTY_264": "Origin",
    "PROPERTY_266": "Product_Keylines",
    "PROPERTY_268": "documents_from_factory",
    "PROPERTY_272": "moq_packaging_matereal",
    "PROPERTY_274": "MOQ_Production",
}


def call_bitrix_api(webhook_url: str, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Call Bitrix API method
    
    Args:
        webhook_url: Bitrix webhook URL (should include /rest/1/webhook_code or similar)
        method: API method name (e.g., 'catalog.product.get')
        params: Method parameters
        
    Returns:
        API response as dictionary or None if error
    """
    # If webhook_url already contains /rest/, use it as is, otherwise append
    if '/rest/' in webhook_url:
        url = f"{webhook_url}/{method}"
    else:
        url = f"{webhook_url}/rest/{method}"
    
    try:
        # Bitrix REST API can use either GET or POST
        # Try GET first (most common)
        response = requests.get(url, params=params, timeout=30)
        
        # If GET fails with 405, try POST
        if response.status_code == 405:
            response = requests.post(url, json=params, timeout=30)
        
        response.raise_for_status()
        result = response.json()
        
        if 'error' in result:
            print(f"API Error: {result.get('error_description', 'Unknown error')}")
            return None
            
        return result
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None


def get_product_from_crm(webhook_url: str, product_id: str) -> Optional[Dict[str, Any]]:
    """
    Get product data from crm.product.get
    
    Args:
        webhook_url: Bitrix webhook URL
        product_id: Product ID
        
    Returns:
        Product data dictionary or None if error
    """
    params = {
        "id": product_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.product.get", params)
    
    if result and 'result' in result:
        return result['result']
    
    return None


def get_product_dates(webhook_url: str, product_id: str) -> Dict[str, Optional[str]]:
    """
    Get dateActiveFrom and dateActiveTo for a product from catalog.product.get
    
    Args:
        webhook_url: Bitrix webhook URL
        product_id: Product ID
        
    Returns:
        Dictionary with dateActiveFrom and dateActiveTo
    """
    params = {
        "id": product_id
    }
    
    result = call_bitrix_api(webhook_url, "catalog.product.get", params)
    
    if result and 'result' in result:
        product_data = result['result']
        return {
            "dateActiveFrom": product_data.get("dateActiveFrom"),
            "dateActiveTo": product_data.get("dateActiveTo")
        }
    
    return {
        "dateActiveFrom": None,
        "dateActiveTo": None
    }


def extract_property_value(property_data: Any) -> Any:
    """
    Extract the actual value from a PROPERTY_* field structure
    
    Args:
        property_data: Property data (can be dict with valueId/value, list, or direct value)
        
    Returns:
        Extracted value
    """
    if property_data is None:
        return None
    
    # If it's a dict with 'value' key, extract the value
    if isinstance(property_data, dict):
        if 'value' in property_data:
            return property_data['value']
        # If no 'value' key, return the dict as is
        return property_data
    
    # If it's a list, process each item
    if isinstance(property_data, list):
        if len(property_data) == 0:
            return None
        # If list contains dicts with 'value', extract values
        if len(property_data) == 1 and isinstance(property_data[0], dict) and 'value' in property_data[0]:
            return property_data[0]['value']
        # For multiple values, return list of extracted values
        return [extract_property_value(item) for item in property_data]
    
    # Otherwise return as is
    return property_data


def remove_id_from_file_objects(data: Any) -> Any:
    """
    Remove 'id' field from file objects (keep only showUrl and downloadUrl)
    
    Args:
        data: Data structure that may contain file objects with 'id' field
        
    Returns:
        Data with 'id' fields removed from file objects
    """
    if data is None:
        return None
    
    # If it's a dict, check if it's a file object (has showUrl or downloadUrl)
    if isinstance(data, dict):
        # Check if this is a file object (has showUrl or downloadUrl)
        if 'showUrl' in data or 'downloadUrl' in data:
            # Remove 'id' field if present
            cleaned = {k: v for k, v in data.items() if k != 'id'}
            return cleaned
        else:
            # Recursively process nested dicts
            return {k: remove_id_from_file_objects(v) for k, v in data.items()}
    
    # If it's a list, process each item
    if isinstance(data, list):
        return [remove_id_from_file_objects(item) for item in data]
    
    # Otherwise return as is
    return data


def map_product_fields(product_data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map product fields using the schema and create readable field names
    Replaces PROPERTY_* fields with readable names (no duplication)
    
    Args:
        product_data: Original product data
        schema: Schema with field definitions
        
    Returns:
        Mapped product data with readable field names (PROPERTY_* fields replaced)
    """
    mapped_data = {}
    
    # First, copy all standard fields (non-PROPERTY_ fields)
    for key, value in product_data.items():
        if not key.startswith("PROPERTY_"):
            mapped_data[key] = value
    
    # Map PROPERTY_* fields to readable names (replace, don't duplicate)
    # Use FIELD_MAPPING first, then fallback to schema title
    for schema_key, field_info in schema.get("result", {}).items():
        if schema_key.startswith("PROPERTY_"):
            # Get readable name from FIELD_MAPPING or schema title
            readable_name = FIELD_MAPPING.get(schema_key)
            if not readable_name:
                # Fallback to schema title, convert to readable format
                field_title = field_info.get("title", "").strip()
                if field_title:
                    # Convert "Country of Origin" -> "Country_of_Origin"
                    readable_name = field_title.replace(" ", "_")
                else:
                    readable_name = schema_key  # Last fallback (keep original if no mapping)
            
            # Extract value from PROPERTY_* field if it exists
            if schema_key in product_data:
                extracted_value = extract_property_value(product_data[schema_key])
                # Add with readable name (replacing PROPERTY_* field)
                mapped_data[readable_name] = extracted_value
                # Do NOT keep the original PROPERTY_* field to avoid duplication
    
    return mapped_data


def process_product(product_id: str, webhook_url: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process product: get all data from crm.product.get, add only dateActiveFrom and dateActiveTo from catalog.product.get
    
    Args:
        product_id: Product ID
        webhook_url: Bitrix webhook URL
        schema: Product schema JSON
        
    Returns:
        Full product data from crm.product.get with dateActiveFrom and dateActiveTo added, and fields mapped
    """
    print(f"Processing product ID: {product_id}")
    
    # Get ALL product data from crm.product.get
    print("Fetching all product data from crm.product.get...")
    product_data = get_product_from_crm(webhook_url, product_id)
    
    if not product_data:
        raise ValueError(f"Product data not found for ID: {product_id}")
    
    print("Product data retrieved successfully")
    
    # Get ONLY dateActiveFrom and dateActiveTo from catalog.product.get
    print("Fetching dateActiveFrom and dateActiveTo from catalog.product.get...")
    dates = get_product_dates(webhook_url, product_id)
    print(f"Retrieved dates: {dates}")
    
    # Add only the two date fields to the product data (preserve all other data from crm.product.get)
    product_data["dateActiveFrom"] = dates["dateActiveFrom"]
    product_data["dateActiveTo"] = dates["dateActiveTo"]
    
    # Map fields using schema (this adds readable field names while keeping all original data)
    mapped_data = map_product_fields(product_data, schema)
    
    # Remove 'id' fields from file objects (keep only showUrl and downloadUrl)
    mapped_data = remove_id_from_file_objects(mapped_data)
    
    return mapped_data


def extract_supplier_id(value: Any) -> Optional[str]:
    """
    Extract supplier ID from various formats
    
    Handles formats like:
    - "38" -> "38"
    - "CO_38" -> "38"
    - "CO_123" -> "123"
    - "AB_456" -> "456"
    - {"value": "CO_38"} -> "38"
    - Any format with underscore: takes the numeric part after the last underscore
    
    Args:
        value: Supplier ID value (can be any format with a numeric ID)
        
    Returns:
        Extracted supplier ID as string or None
    """
    if value is None:
        return None
    
    # Convert to string first
    value_str = str(value).strip()
    
    if not value_str:
        return None
    
    # Handle format like "CO_38", "AB_123", etc. - extract the number after underscore
    if "_" in value_str:
        parts = value_str.split("_")
        # Take the last part (should be the ID)
        if len(parts) > 1:
            value_str = parts[-1]
    
    # Extract digits only (handles any numeric ID)
    # This will extract "38" from "CO_38", "123" from "CO_123", etc.
    match = re.search(r'\d+', value_str)
    if match:
        return match.group(0)
    
    # If no digits found, return the original string (might be a valid non-numeric ID)
    return value_str if value_str else None


def create_supplier_mapping(product_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create supplier_product_mapping entry
    
    Args:
        product_data: Product data
        
    Returns:
        Mapping dictionary with product_id and supplier_id
    """
    product_id = product_data.get("ID")
    
    # Try to get Factory from multiple possible locations
    supplier_id = None
    
    # First try direct "Factory" field (if already mapped)
    if "Factory" in product_data:
        supplier_id = product_data.get("Factory")
    
    # If not found, try PROPERTY_108 (Factory property)
    if not supplier_id and "PROPERTY_108" in product_data:
        supplier_id = extract_property_value(product_data.get("PROPERTY_108"))
    
    # If still not found, try the readable mapped field
    if not supplier_id:
        # Check if Factory was mapped to a readable name
        for key, value in product_data.items():
            if key in ["Factory", "PROPERTY_108"] or (isinstance(key, str) and "factory" in key.lower()):
                supplier_id = value
                break
    
    if not product_id:
        raise ValueError("Product ID not found")
    
    if not supplier_id:
        print(f"Warning: Factory (supplier_id) not found for product {product_id}")
        supplier_id_str = None
    else:
        # Extract supplier ID from various formats (e.g., "CO_38" -> "38")
        supplier_id_str = extract_supplier_id(supplier_id)
    
    return {
        "product_id": str(product_id),
        "supplier_id": supplier_id_str
    }


def create_logistic_data(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create logistic data from product fields
    Always includes all 12 fields (empty fields will be null or empty array)
    
    Args:
        product_data: Product data with mapped fields
        
    Returns:
        Dictionary with logistic information (all 12 fields always present)
    """
    logistic = {}
    
    # Map product fields to logistic fields
    # Cartons_per_Pallet -> cartons_per_pallet
    cartons_per_pallet = product_data.get("Cartons_per_Pallet") or product_data.get("PROPERTY_192")
    if cartons_per_pallet:
        # Extract numeric value if it's a string like "81 cartons - 1134 pieces"
        if isinstance(cartons_per_pallet, str):
            # Try to extract number before "carton" or first number
            import re
            match = re.search(r'(\d+)\s*carton', cartons_per_pallet, re.IGNORECASE)
            if match:
                logistic["cartons_per_pallet"] = int(match.group(1))
            else:
                # Try to extract first number
                match = re.search(r'\d+', cartons_per_pallet)
                if match:
                    logistic["cartons_per_pallet"] = int(match.group(0))
                else:
                    # If no number found, keep the original string value
                    logistic["cartons_per_pallet"] = cartons_per_pallet
        elif isinstance(cartons_per_pallet, (int, float)):
            logistic["cartons_per_pallet"] = int(cartons_per_pallet)
        else:
            logistic["cartons_per_pallet"] = str(cartons_per_pallet)
    else:
        logistic["cartons_per_pallet"] = None
    
    # Loading_Quantities -> loading_quantities
    loading_quantities = product_data.get("Loading_Quantities") or product_data.get("PROPERTY_166")
    if loading_quantities:
        if isinstance(loading_quantities, str):
            # Try to parse as JSON array or split by common delimiters
            try:
                import json
                logistic["loading_quantities"] = json.loads(loading_quantities)
            except:
                # Split by comma, semicolon, or newline
                quantities = [q.strip() for q in loading_quantities.replace(';', ',').replace('\n', ',').split(',') if q.strip()]
                logistic["loading_quantities"] = quantities if quantities else [loading_quantities]
        elif isinstance(loading_quantities, list):
            logistic["loading_quantities"] = loading_quantities
        else:
            logistic["loading_quantities"] = [str(loading_quantities)]
    else:
        logistic["loading_quantities"] = []
    
    # transport_conditions_temperature -> transport_delivery_conditions_temperature
    transport_temp = product_data.get("transport_conditions_temperature") or product_data.get("Transport_Temperature") or product_data.get("PROPERTY_216")
    if transport_temp:
        logistic["transport_delivery_conditions_temperature"] = str(transport_temp)
    else:
        logistic["transport_delivery_conditions_temperature"] = None
    
    # storage_conditions_temperature -> storage_conditions_temperature
    storage_temp = product_data.get("storage_conditions_temperature") or product_data.get("Storage_Temperature") or product_data.get("PROPERTY_218")
    if storage_temp:
        logistic["storage_conditions_temperature"] = str(storage_temp)
    else:
        logistic["storage_conditions_temperature"] = None
    
    # Carton_Dimensions -> carton_dimensions
    carton_dims = product_data.get("Carton_Dimensions") or product_data.get("PROPERTY_220")
    if carton_dims:
        logistic["carton_dimensions"] = str(carton_dims)
    else:
        logistic["carton_dimensions"] = None
    
    # Pallet_Dimensions -> pallet_dimensions
    pallet_dims = product_data.get("Pallet_Dimensions") or product_data.get("PROPERTY_222")
    if pallet_dims:
        logistic["pallet_dimensions"] = str(pallet_dims)
    else:
        logistic["pallet_dimensions"] = None
    
    # Term_of_Delivery -> term_of_delivery
    term_delivery = product_data.get("Term_of_Delivery") or product_data.get("PROPERTY_254")
    if term_delivery:
        logistic["term_of_delivery"] = str(term_delivery)
    else:
        logistic["term_of_delivery"] = None
    
    # Loading_Address -> loading_address
    loading_address = product_data.get("Loading_Address") or product_data.get("PROPERTY_242")
    if loading_address:
        logistic["loading_address"] = str(loading_address)
    else:
        logistic["loading_address"] = None
    
    # Lead_Time_Print_Packing -> lead_time_to_print_packing_material
    lead_time_print = product_data.get("Lead_Time_Print_Packing") or product_data.get("PROPERTY_228")
    if lead_time_print:
        logistic["lead_time_to_print_packing_material"] = str(lead_time_print)
    else:
        logistic["lead_time_to_print_packing_material"] = None
    
    # Lead_Time_Reorder_Packing -> lead_time_to_reorder_packing_material
    lead_time_reorder = product_data.get("Lead_Time_Reorder_Packing") or product_data.get("PROPERTY_230")
    if lead_time_reorder:
        logistic["lead_time_to_reorder_packing_material"] = str(lead_time_reorder)
    else:
        logistic["lead_time_to_reorder_packing_material"] = None
    
    # moq_packaging_matereal -> moq_packaging_matereal
    moq_packaging = product_data.get("moq_packaging_matereal") or product_data.get("MOQ_Packaging_Material") or product_data.get("PROPERTY_272")
    if moq_packaging:
        # Extract numeric value if it's a number or string
        if isinstance(moq_packaging, (int, float)):
            logistic["moq_packaging_matereal"] = int(moq_packaging)
        else:
            logistic["moq_packaging_matereal"] = str(moq_packaging)
    else:
        logistic["moq_packaging_matereal"] = None
    
    # MOQ_Production -> moq_production
    moq_production = product_data.get("MOQ_Production") or product_data.get("PROPERTY_274")
    if moq_production:
        # Extract numeric value if it's a number or string
        if isinstance(moq_production, (int, float)):
            logistic["moq_production"] = int(moq_production)
        else:
            logistic["moq_production"] = str(moq_production)
    else:
        logistic["moq_production"] = None
    
    return logistic


def process_product_data(input_data) -> Dict[str, Any]:
    """
    Main function to process product data - can be used by backend
    
    Args:
        input_data: Can be either:
            - Product ID (string or integer): "8038" or 8038
            - Dictionary with structure: {"id": "8038", "eventtype": "UPDATE", "table": "product"}
        
    Returns:
        Dictionary with structure:
        {
            "product": { ... all product data ... },
            "mapping": {
                "product_id": [123],
                "supplier_id": [38]
            },
            "logistic": {
                "cartons_per_pallet": 72,
                "loading_quantities": [...],
                ...
            },
            "eventtype": "UPDATE",  # If provided in input
            "table": "product"      # If provided in input
        }
        
    Raises:
        ValueError: If product_id is invalid or product not found
        RuntimeError: If BITRIX_WEBHOOK_URL is not configured
    """
    # Extract product_id and additional fields from input
    product_id = None
    eventtype = None
    table = None
    
    # Handle different input formats
    if isinstance(input_data, dict):
        # Input is a dictionary with id, eventtype, table
        product_id = input_data.get("id") or input_data.get("ID")
        eventtype = input_data.get("eventtype")
        table = input_data.get("table")
    else:
        # Input is just a product ID (string or integer)
        product_id = input_data
    
    # Convert product_id to string if it's an integer
    product_id = str(product_id) if product_id is not None else None
    
    # Use the BITRIX_WEBHOOK_URL defined at module level
    if not BITRIX_WEBHOOK_URL:
        raise RuntimeError(
            "BITRIX_WEBHOOK_URL is not configured. "
            "Please set it in the process_product.py file at the top."
        )
    
    if not product_id or not product_id.strip():
        raise ValueError("Product ID is required")
    
    # Load schema
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(script_dir, "product_schema.json")
    
    if os.path.exists(schema_file):
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    else:
        # Use empty schema if file doesn't exist
        schema = {"result": {}}
    
    # Process product
    processed_product = process_product(product_id, BITRIX_WEBHOOK_URL, schema)
    
    # Create supplier mapping (use processed_product which has mapped Factory field)
    supplier_mapping = create_supplier_mapping(processed_product)
    
    # Create logistic data
    logistic_data = create_logistic_data(processed_product)
    
    # Create single output JSON with product, mapping, and logistic
    output_data = {
        "product": processed_product,
        "mapping": {
            "product_id": [int(supplier_mapping["product_id"])] if supplier_mapping["product_id"] else [],
            "supplier_id": [int(supplier_mapping["supplier_id"])] if supplier_mapping["supplier_id"] else []
        },
        "logistic": logistic_data,
        "webhook": "bitrix"
    }
    
    # Add eventtype and table if provided in input (preserve as-is)
    if eventtype is not None:
        output_data["eventtype"] = eventtype
    if table is not None:
        output_data["table"] = table
    
    return output_data


# def main():
#     """
#     CLI entry point for processing product data
#     """
#     # Configuration - load from environment variable or .env file
#     # (dotenv is already loaded at module level if available)
#     BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL", "")
    
#     if not BITRIX_WEBHOOK_URL:
#         print("Error: BITRIX_WEBHOOK_URL not found")
#         print("Please set it in one of the following ways:")
#         print("1. Create a .env file with: BITRIX_WEBHOOK_URL='https://dana.bitrix24.eu/rest/218/8cxeo979k998jzqq/'")
#         print("2. Or set environment variable: export BITRIX_WEBHOOK_URL='https://dana.bitrix24.eu/rest/218/8cxeo979k998jzqq/'")
#         sys.exit(1)
    
#     # Get product ID from command line argument or stdin
#     if len(sys.argv) > 1:
#         # Product ID from command line argument
#         product_id = sys.argv[1]
#     else:
#         # Read product ID from stdin
#         print("Enter product ID: ", end='', flush=True)
#         product_id = sys.stdin.readline().strip()
    
#     if not product_id:
#         print("Error: Product ID is required")
#         print("Usage: python process_product.py <product_id>")
#         print("   or: echo '8034' | python process_product.py")
#         sys.exit(1)
    
#     # Process product using the main function
#     try:
#         output_data = process_product_data(product_id)
        
#         # Write to single output file
#         output_file = "output.json"
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(output_data, f, indent=2, ensure_ascii=False)
#         print(f"\nOutput saved to: {output_file}")
        
#         # Print summary
#         print("\n=== Summary ===")
#         print(f"Product ID: {output_data['product'].get('ID')}")
#         print(f"Product Name: {output_data['product'].get('NAME')}")
#         print(f"Date Active From: {output_data['product'].get('dateActiveFrom')}")
#         print(f"Date Active To: {output_data['product'].get('dateActiveTo')}")
#         print(f"Supplier ID: {output_data['mapping']['supplier_id']}")
        
#     except Exception as e:
#         print(f"Error processing product: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)


# if __name__ == "__main__":
#     main()

# Direct function call - can be used by backend or run directly
if __name__ == "__main__":
    try:
        # Example: process product with input JSON
        input_data = {
            "id": "8038",
            "eventtype": "UPDATE",
            "table": "product"
        }
        output_data = process_product_data(input_data)
        print(output_data)
        
        # Save output to file
        output_file = "output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nOutput saved to: {output_file}")
        
        # Print summary
        print("\n=== Summary ===")
        print(f"Product ID: {output_data['product'].get('ID')}")
        print(f"Product Name: {output_data['product'].get('NAME')}")
        print(f"Date Active From: {output_data['product'].get('dateActiveFrom')}")
        print(f"Date Active To: {output_data['product'].get('dateActiveTo')}")
        print(f"Supplier ID: {output_data['mapping']['supplier_id']}")
        if 'eventtype' in output_data:
            print(f"Event Type: {output_data['eventtype']}")
        if 'table' in output_data:
            print(f"Table: {output_data['table']}")
        
    except Exception as e:
        print(f"Error processing product: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)