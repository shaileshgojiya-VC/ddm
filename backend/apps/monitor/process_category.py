#!/usr/bin/env python3
"""
Script to process category (product section) data:
1. Extract category ID from input
2. Call crm.productsection.get to get category data
3. Return processed JSON with category data
"""

import json
import os
import sys
import requests
from typing import Dict, Any, Optional

# Bitrix webhook URL - configured directly in this file
BITRIX_WEBHOOK_URL = "https://dana.bitrix24.eu/rest/218/8cxeo979k998jzqq/"


def call_bitrix_api(webhook_url: str, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Call Bitrix API method
    
    Args:
        webhook_url: Bitrix webhook URL
        method: API method name (e.g., 'crm.productsection.get')
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


def rename_category_fields(mapped_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rename specific category fields to standardized names
    
    Args:
        mapped_data: Mapped category data
        
    Returns:
        Category data with renamed fields
    """
    # Field rename mapping: old_name -> new_name
    field_renames = {
        "ID": "bitrix_id",
        "Catalog": "catelog_id",
        "CATALOG_ID": "catelog_id",
        "Section": "section_id",
        "SECTION_ID": "section_id",
        "Name": "name",
        "NAME": "name",
        "Mnemonic_code": "code",
        "CODE": "code",
        "External_ID": "external_id",
        "XML_ID": "external_id"
    }
    
    # Create new dictionary with renamed fields
    renamed_data = {}
    for key, value in mapped_data.items():
        if key in field_renames:
            # Use the new name
            new_key = field_renames[key]
            renamed_data[new_key] = value
        else:
            # Keep original key
            renamed_data[key] = value
    
    return renamed_data


def map_category_fields(category_data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map category fields using the schema and create readable field names
    Uses listLabel if available, otherwise uses title
    
    Args:
        category_data: Original category data
        schema: Schema with field definitions
        
    Returns:
        Mapped category data with readable field names
    """
    mapped_data = {}
    schema_result = schema.get("result", {})
    mapped_standard_fields = set()  # Track which standard fields we've mapped
    
    # Map all fields from schema
    for schema_key, field_info in schema_result.items():
        # Get readable name: prioritize listLabel, then formLabel, then title
        field_label = field_info.get("listLabel", "").strip()
        if not field_label:
            field_label = field_info.get("formLabel", "").strip()
        if not field_label:
            field_label = field_info.get("title", "").strip()
        
        if field_label:
            # Convert "Field Name" -> "Field_Name"
            readable_name = field_label.replace(" ", "_")
        else:
            readable_name = schema_key  # Keep original if no label
        
        # Extract value from field if it exists in category_data
        if schema_key in category_data:
            value = category_data[schema_key]
            
            # Map standard fields with readable name (if different from original)
            if readable_name != schema_key:
                mapped_data[readable_name] = value
                mapped_standard_fields.add(schema_key)
            else:
                # Keep original name if no mapping
                mapped_data[schema_key] = value
                mapped_standard_fields.add(schema_key)
    
    # Add any fields that weren't in the schema (keep original names)
    for key, value in category_data.items():
        if key not in mapped_standard_fields:
            mapped_data[key] = value
    
    return mapped_data


def get_category_from_crm(webhook_url: str, category_id: str) -> Optional[Dict[str, Any]]:
    """
    Get category data from crm.productsection.get
    
    Args:
        webhook_url: Bitrix webhook URL
        category_id: Category ID
        
    Returns:
        Category data dictionary or None if error
    """
    params = {
        "id": category_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.productsection.get", params)
    
    if result and 'result' in result:
        return result['result']
    
    return None


def process_category(category_id: str, webhook_url: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process category: get all data from crm.productsection.get and map fields
    
    Args:
        category_id: Category ID
        webhook_url: Bitrix webhook URL
        schema: Category schema JSON
        
    Returns:
        Full category data from crm.productsection.get with mapped fields
    """
    print(f"Processing category ID: {category_id}")
    
    # Get ALL category data from crm.productsection.get
    print("Fetching all category data from crm.productsection.get...")
    category_data = get_category_from_crm(webhook_url, category_id)
    
    if not category_data:
        raise ValueError(f"Category data not found for ID: {category_id}")
    
    print("Category data retrieved successfully")
    
    # Map fields using schema
    mapped_data = map_category_fields(category_data, schema)
    
    # Rename specific fields to standardized names
    mapped_data = rename_category_fields(mapped_data)
    
    return mapped_data


def process_category_data(input_data) -> Dict[str, Any]:
    """
    Main function to process category data - can be used by backend
    
    Args:
        input_data: Can be either:
            - Category ID (string or integer): "128" or 128
            - Dictionary with structure: {"id": "128", "eventtype": "UPDATE", "table": "category"}
        
    Returns:
        Dictionary with processed category data including:
        - All category fields from crm.productsection.get
        - eventtype: "UPDATE" (if provided in input)
        - table: "category" (if provided in input)
        - webhook: "bitrix"
        
    Raises:
        ValueError: If category_id is invalid or category not found
        RuntimeError: If BITRIX_WEBHOOK_URL is not configured
    """
    # Extract category_id and additional fields from input
    category_id = None
    eventtype = None
    table = None
    
    # Handle different input formats
    if isinstance(input_data, dict):
        # Input is a dictionary with id, eventtype, table
        category_id = input_data.get("id") or input_data.get("ID")
        eventtype = input_data.get("eventtype")
        table = input_data.get("table")
    else:
        # Input is just a category ID (string or integer)
        category_id = input_data
    
    # Convert category_id to string if it's an integer
    category_id = str(category_id) if category_id is not None else None
    
    # Use the BITRIX_WEBHOOK_URL defined at module level
    if not BITRIX_WEBHOOK_URL:
        raise RuntimeError(
            "BITRIX_WEBHOOK_URL is not configured. "
            "Please set it in the process_category.py file at the top."
        )
    
    if not category_id or not category_id.strip():
        raise ValueError("Category ID is required")
    
    # Load schema
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(script_dir, "category_schema.json")
    
    if os.path.exists(schema_file):
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    else:
        # Use empty schema if file doesn't exist
        print(f"Warning: Schema file '{schema_file}' not found. Using empty schema.")
        schema = {"result": {}}
    
    # Process category
    processed_category = process_category(category_id, BITRIX_WEBHOOK_URL, schema)
    
    # Add eventtype and table if provided in input (preserve as-is)
    if eventtype is not None:
        processed_category["eventtype"] = eventtype
    if table is not None:
        processed_category["table"] = table
    
    # Add webhook field
    processed_category["webhook"] = "bitrix"
    
    return processed_category


# Direct function call - can be used by backend or run directly
if __name__ == "__main__":
    try:
        # Example: process category with input JSON
        input_data = {
            "id": "132",
            "eventtype": "UPDATE",
            "table": "category"
        }
        output_data = process_category_data(input_data)
        
        # Save output to file
        output_file = "output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nOutput saved to: {output_file}")
        
        # Print summary
        print("\n=== Summary ===")
        print(f"Category ID: {output_data.get('ID')}")
        print(f"Category Name: {output_data.get('NAME')}")
        print(f"Catalog ID: {output_data.get('CATALOG_ID')}")
        if 'eventtype' in output_data:
            print(f"Event Type: {output_data['eventtype']}")
        if 'table' in output_data:
            print(f"Table: {output_data['table']}")
        if 'webhook' in output_data:
            print(f"Webhook: {output_data['webhook']}")
        
    except Exception as e:
        print(f"Error processing category: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

