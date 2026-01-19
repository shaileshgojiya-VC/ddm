#!/usr/bin/env python3
"""
Script to process company data:
1. Extract company ID from input
2. Call crm.requisite.list to get requisites
3. Extract registration number (UF_CRM_1637925689) and VAT number (RQ_VAT_ID)
4. Add these fields to the company data
5. Create full updated JSON
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
        method: API method name (e.g., 'crm.requisite.list')
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


def get_company_from_crm(webhook_url: str, company_id: str) -> Optional[Dict[str, Any]]:
    """
    Get company data from crm.company.get
    
    Args:
        webhook_url: Bitrix webhook URL
        company_id: Company ID
        
    Returns:
        Company data dictionary or None if error
    """
    params = {
        "id": company_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.company.get", params)
    
    if result and 'result' in result:
        return result['result']
    
    return None


def get_company_requisites(webhook_url: str, company_id: str) -> Dict[str, Optional[str]]:
    """
    Get requisites for a company and extract registration number and VAT number
    
    Args:
        webhook_url: Bitrix webhook URL
        company_id: Company ID
        
    Returns:
        Dictionary with registration_number and vat_number
    """
    params = {
        "filter": {
            "ENTITY_TYPE_ID": 4,  # 4 is for Company
            "ENTITY_ID": company_id
        }
    }
    
    result = call_bitrix_api(webhook_url, "crm.requisite.list", params)
    
    registration_number = None
    vat_number = None
    
    if result and 'result' in result:
        requisites = result['result']
        
        # Handle both list and dict formats
        if isinstance(requisites, list):
            # Process all requisites, use the first one with data
            for requisite in requisites:
                # Extract registration number from UF_CRM_1637925689
                if 'UF_CRM_1637925689' in requisite:
                    reg_num = requisite['UF_CRM_1637925689']
                    if reg_num and not registration_number:
                        registration_number = str(reg_num) if reg_num else None
                
                # Extract VAT number from RQ_VAT_ID
                if 'RQ_VAT_ID' in requisite:
                    vat = requisite['RQ_VAT_ID']
                    if vat and not vat_number:
                        vat_number = str(vat) if vat else None
                
                # If we found both, we can break
                if registration_number and vat_number:
                    break
        elif isinstance(requisites, dict):
            # Single requisite or dict format
            if 'UF_CRM_1637925689' in requisites:
                reg_num = requisites['UF_CRM_1637925689']
                registration_number = str(reg_num) if reg_num else None
            
            if 'RQ_VAT_ID' in requisites:
                vat = requisites['RQ_VAT_ID']
                vat_number = str(vat) if vat else None
    
    return {
        "registration_number": registration_number,
        "vat_number": vat_number
    }


def extract_property_value(property_data: Any) -> Any:
    """
    Extract the actual value from a field structure
    
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


def rename_company_fields(mapped_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rename specific company fields to standardized names
    
    Args:
        mapped_data: Mapped company data
        
    Returns:
        Company data with renamed fields
    """
    # Field rename mapping: old_name -> new_name
    field_renames = {
        "State_/_Province": "state",
        "Billing_State_/_Province": "billing_state",
        "Item_ID_in_data_source": "item_id_in_data_source",  # Keeping it since user put "?" - can be changed if needed
        "E-mail": "email",
        "#TAG": "hashtag",
        "Annual_Order_Volume_(FCLs)": "annual_order_volume",
        "Date_of_Inquiry_(inquiry_date_/_cold_contact_date)": "date_of_inquiry",
        "Factory_certificates:__a._ISO____b._HACCP____b._FSSC____c._GMP___d.\tLICENSE": "factory_certificates",
        "vat_number": "rq_vat_id"
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


def map_company_fields(company_data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map company fields using the schema and create readable field names
    Uses listLabel if available, otherwise uses title
    Maps all UF_CRM_* fields to readable names (mapped if in schema, original name if not)
    
    Args:
        company_data: Original company data
        schema: Schema with field definitions
        
    Returns:
        Mapped company data with readable field names
    """
    mapped_data = {}
    schema_result = schema.get("result", {})
    mapped_uf_fields = set()  # Track which UF_CRM_* fields we've mapped
    mapped_standard_fields = set()  # Track which standard fields we've mapped
    
    # Map all fields from schema (standard and UF_CRM_*)
    for schema_key, field_info in schema_result.items():
        # Get readable name: prioritize listLabel, then title
        field_label = field_info.get("listLabel", "").strip()
        if not field_label:
            field_label = field_info.get("title", "").strip()
        
        if field_label:
            # Convert "Field Name" -> "Field_Name"
            readable_name = field_label.replace(" ", "_")
        else:
            readable_name = schema_key  # Keep original if no label
        
        # Extract value from field if it exists in company_data
        if schema_key in company_data:
            extracted_value = extract_property_value(company_data[schema_key])
            
            if schema_key.startswith("UF_CRM_"):
                # Map UF_CRM_* fields with readable name
                mapped_data[readable_name] = extracted_value
                mapped_uf_fields.add(schema_key)
            else:
                # Map standard fields with readable name (if different from original)
                if readable_name != schema_key:
                    mapped_data[readable_name] = extracted_value
                    mapped_standard_fields.add(schema_key)
                else:
                    # Keep original name if no mapping
                    mapped_data[schema_key] = extracted_value
                    mapped_standard_fields.add(schema_key)
    
    # Add any standard fields that weren't in the schema (keep original names)
    for key, value in company_data.items():
        if not key.startswith("UF_CRM_"):
            if key not in mapped_standard_fields:
                mapped_data[key] = value
    
    # Add any UF_CRM_* fields that weren't in the schema (keep original names)
    for key, value in company_data.items():
        if key.startswith("UF_CRM_") and key not in mapped_uf_fields:
            # Keep the original UF_CRM_* field name if not in schema
            mapped_data[key] = value
    
    return mapped_data


def process_company(company_id: str, webhook_url: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process company: get all data from crm.company.get, get requisites, and map fields
    
    Args:
        company_id: Company ID
        webhook_url: Bitrix webhook URL
        schema: Company schema JSON
        
    Returns:
        Full company data with registration_number, vat_number, and mapped fields
    """
    print(f"Processing company ID: {company_id}")
    
    # Get ALL company data from crm.company.get
    print("Fetching all company data from crm.company.get...")
    company_data = get_company_from_crm(webhook_url, company_id)
    
    if not company_data:
        raise ValueError(f"Company data not found for ID: {company_id}")
    
    print("Company data retrieved successfully")
    
    # Get requisites
    print("Fetching requisites from crm.requisite.list...")
    requisites = get_company_requisites(webhook_url, company_id)
    print(f"Retrieved requisites: {requisites}")
    
    # Add requisites to company data
    company_data["registration_number"] = requisites["registration_number"]
    company_data["vat_number"] = requisites["vat_number"]
    
    # Map fields using schema
    mapped_data = map_company_fields(company_data, schema)
    
    # Rename specific fields to standardized names
    mapped_data = rename_company_fields(mapped_data)
    
    return mapped_data


def process_company_data(input_data) -> Dict[str, Any]:
    """
    Main function to process company data - can be used by backend
    
    Args:
        input_data: Can be either:
            - Company ID (string or integer): "21810" or 21810
            - Dictionary with structure: {"id": "21810", "eventtype": "UPDATE", "table": "company"}
        
    Returns:
        Dictionary with processed company data including:
        - All company fields from crm.company.get
        - registration_number (from requisites)
        - vat_number (from requisites)
        - Mapped fields according to schema
        - eventtype: "UPDATE" (if provided in input)
        - table: "company" (if provided in input)
        
    Raises:
        ValueError: If company_id is invalid or company not found
        RuntimeError: If BITRIX_WEBHOOK_URL is not configured
    """
    # Extract company_id and additional fields from input
    company_id = None
    eventtype = None
    table = None
    
    # Handle different input formats
    if isinstance(input_data, dict):
        # Input is a dictionary with id, eventtype, table
        company_id = input_data.get("id") or input_data.get("ID")
        eventtype = input_data.get("eventtype")
        table = input_data.get("table")
    else:
        # Input is just a company ID (string or integer)
        company_id = input_data
    
    # Convert company_id to string if it's an integer
    company_id = str(company_id) if company_id is not None else None
    
    # Use the BITRIX_WEBHOOK_URL defined at module level
    if not BITRIX_WEBHOOK_URL:
        raise RuntimeError(
            "BITRIX_WEBHOOK_URL is not configured. "
            "Please set it in the process_company.py file at the top."
        )
    
    if not company_id or not company_id.strip():
        raise ValueError("Company ID is required")
    
    # Load schema
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Try both schema file names (with and without " 1")
    schema_file = os.path.join(script_dir, "company_schema 1.json")
    if not os.path.exists(schema_file):
        schema_file = os.path.join(script_dir, "company_schema.json")
    
    if os.path.exists(schema_file):
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    else:
        # Use empty schema if file doesn't exist
        print(f"Warning: Schema file '{schema_file}' not found. Using empty schema.")
        schema = {"result": {}}
    
    # Process company
    processed_company = process_company(company_id, BITRIX_WEBHOOK_URL, schema)
    
    # Add eventtype and table if provided in input (preserve as-is)
    if eventtype is not None:
        processed_company["eventtype"] = eventtype
    if table is not None:
        processed_company["table"] = table
    
    # Add webhook field
    processed_company["webhook"] = "bitrix"
    
    return processed_company


# def main():
#     """
#     CLI entry point for processing company data
#     """
#     # Get company ID from command line argument or stdin
#     if len(sys.argv) > 1:
#         # Company ID from command line argument
#         company_id = sys.argv[1]
#     else:
#         # Read company ID from stdin
#         print("Enter company ID: ", end='', flush=True)
#         company_id = sys.stdin.readline().strip()
#     
#     if not company_id:
#         print("Error: Company ID is required")
#         print("Usage: python process_company.py <company_id>")
#         print("   or: echo '123' | python process_company.py")
#         sys.exit(1)
#     
#     # Process company using the main function
#     try:
#         output_data = process_company_data(company_id)
#         
#         # Write to output file
#         output_file = "output.json"
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(output_data, f, indent=2, ensure_ascii=False)
#         print(f"\nOutput saved to: {output_file}")
#         
#         # Print summary
#         print("\n=== Summary ===")
#         print(f"Company ID: {output_data.get('ID')}")
#         print(f"Company Title: {output_data.get('TITLE')}")
#         print(f"Registration Number: {output_data.get('registration_number')}")
#         print(f"VAT Number: {output_data.get('vat_number')}")
#         
#     except Exception as e:
#         print(f"Error processing company: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)


# Direct function call - can be used by backend or run directly
if __name__ == "__main__":
    try:
        # Example: process company with input JSON
        input_data = {
            "id": "266",
            "eventtype": "UPDATE",
            "table": "company"
        }
        output_data = process_company_data(input_data)
        
        # Save output to file
        output_file = "output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nOutput saved to: {output_file}")
        
        # Print summary
        print("\n=== Summary ===")
        print(f"Company ID: {output_data.get('ID')}")
        print(f"Company Name: {output_data.get('Company_Name')}")
        print(f"Registration Number: {output_data.get('registration_number')}")
        print(f"VAT Number: {output_data.get('vat_number')}")
        if 'eventtype' in output_data:
            print(f"Event Type: {output_data['eventtype']}")
        if 'table' in output_data:
            print(f"Table: {output_data['table']}")
        
    except Exception as e:
        print(f"Error processing company: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

