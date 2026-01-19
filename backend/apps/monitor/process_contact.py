#!/usr/bin/env python3
"""
Script to process contact data:
1. Extract contact ID from input
2. Call crm.contact.get to get contact data
3. Merge NAME, SECOND_NAME, and LAST_NAME into full_name
4. Return processed JSON with contact data
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
        method: API method name (e.g., 'crm.contact.get')
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


def extract_email_from_data(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract email from EMAIL field (can be list or dict format)
    
    Args:
        data: Data dictionary with EMAIL field
        
    Returns:
        First email address found or None
    """
    email = data.get("EMAIL")
    if not email:
        return None
    
    # Handle list format [{"ID": "33292", "VALUE_TYPE": "WORK", "VALUE": "email@example.com", "TYPE_ID": "EMAIL"}]
    if isinstance(email, list):
        for e in email:
            if isinstance(e, dict):
                email_value = e.get("VALUE")
                if email_value:
                    return str(email_value)
            else:
                return str(e)
    elif isinstance(email, dict):
        email_value = email.get("VALUE")
        if email_value:
            return str(email_value)
    else:
        return str(email)
    
    return None


def get_contact_from_crm(webhook_url: str, contact_id: str) -> Optional[Dict[str, Any]]:
    """
    Get contact data from crm.contact.get
    
    Args:
        webhook_url: Bitrix webhook URL
        contact_id: Contact ID
        
    Returns:
        Contact data dictionary or None if error
    """
    params = {
        "id": contact_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.contact.get", params)
    
    if result and 'result' in result:
        return result['result']
    
    return None


def create_full_name(contact_data: Dict[str, Any]) -> str:
    """
    Merge NAME, SECOND_NAME, and LAST_NAME into full_name
    
    Args:
        contact_data: Contact data dictionary
        
    Returns:
        Full name string
    """
    name_parts = []
    
    # Add NAME if present
    name = contact_data.get("NAME")
    if name and str(name).strip():
        name_parts.append(str(name).strip())
    
    # Add SECOND_NAME if present
    second_name = contact_data.get("SECOND_NAME")
    if second_name and str(second_name).strip():
        name_parts.append(str(second_name).strip())
    
    # Add LAST_NAME if present
    last_name = contact_data.get("LAST_NAME")
    if last_name and str(last_name).strip():
        name_parts.append(str(last_name).strip())
    
    # Join all parts with space
    full_name = " ".join(name_parts) if name_parts else ""
    
    return full_name


def process_contact(contact_id: str, webhook_url: str) -> Dict[str, Any]:
    """
    Process contact: get all data from crm.contact.get, add full_name, email, and company_name
    
    Args:
        contact_id: Contact ID
        webhook_url: Bitrix webhook URL
        
    Returns:
        Dictionary with full_name, email, and company_name
    """
    print(f"Processing contact ID: {contact_id}")
    
    # Get ALL contact data from crm.contact.get
    print("Fetching all contact data from crm.contact.get...")
    contact_data = get_contact_from_crm(webhook_url, contact_id)
    
    if not contact_data:
        raise ValueError(f"Contact data not found for ID: {contact_id}")
    
    print("Contact data retrieved successfully")
    
    # Create full_name from NAME, SECOND_NAME, and LAST_NAME
    full_name = create_full_name(contact_data)
    print(f"Full name created: {full_name}")
    
    # Extract email from contact
    email = extract_email_from_data(contact_data)
    print(f"Email from contact: {email}")
    
    # If email not found, try to get from company
    if not email:
        company_id = contact_data.get("COMPANY_ID")
        if company_id:
            print(f"No email in contact, trying company ID: {company_id}")
            company_data = get_company_from_crm(webhook_url, str(company_id))
            if company_data:
                email = extract_email_from_data(company_data)
                print(f"Email from company: {email}")
    
    # Get company name and company_type
    company_name = None
    company_type = None
    company_id = contact_data.get("COMPANY_ID")
    if company_id:
        print(f"Fetching company data for company ID: {company_id}")
        company_data = get_company_from_crm(webhook_url, str(company_id))
        if company_data:
            company_name = company_data.get("TITLE")
            print(f"Company name: {company_name}")
            
            # Get company_type from company
            company_type = company_data.get("COMPANY_TYPE")
            if company_type:
                # Handle if it's a dict with ID or VALUE
                if isinstance(company_type, dict):
                    company_type = company_type.get("ID") or company_type.get("VALUE") or str(company_type)
                else:
                    company_type = str(company_type)
                print(f"Company type: {company_type}")
    
    return {
        "full_name": full_name,
        "email": email,
        "company_name": company_name,
        "company_type": company_type
    }


def process_contact_data(input_data) -> Dict[str, Any]:
    """
    Main function to process contact data - can be used by backend
    
    Args:
        input_data: Can be either:
            - Contact ID (string or integer): "25128" or 25128
            - Dictionary with structure: {"id": "25128", "eventtype": "UPDATE", "table": "contact"}
        
    Returns:
        Dictionary with processed contact data including:
        - All contact fields from crm.contact.get
        - full_name (merged from NAME, SECOND_NAME, LAST_NAME)
        - eventtype: "UPDATE" (if provided in input)
        - table: "contact" (if provided in input)
        - webhook: "bitrix"
        
    Raises:
        ValueError: If contact_id is invalid or contact not found
        RuntimeError: If BITRIX_WEBHOOK_URL is not configured
    """
    # Extract contact_id and additional fields from input
    contact_id = None
    eventtype = None
    table = None
    
    # Handle different input formats
    if isinstance(input_data, dict):
        # Input is a dictionary with id, eventtype, table
        contact_id = input_data.get("id") or input_data.get("ID")
        eventtype = input_data.get("eventtype")
        table = input_data.get("table")
    else:
        # Input is just a contact ID (string or integer)
        contact_id = input_data
    
    # Convert contact_id to string if it's an integer
    contact_id = str(contact_id) if contact_id is not None else None
    
    # Use the BITRIX_WEBHOOK_URL defined at module level
    if not BITRIX_WEBHOOK_URL:
        raise RuntimeError(
            "BITRIX_WEBHOOK_URL is not configured. "
            "Please set it in the process_contact.py file at the top."
        )
    
    if not contact_id or not contact_id.strip():
        raise ValueError("Contact ID is required")
    
    # Process contact to get full_name, email, and company_name
    processed_contact = process_contact(contact_id, BITRIX_WEBHOOK_URL)
    
    # Create minimal output with only required fields
    output_data = {
        "id": contact_id,
        "full_name": processed_contact.get("full_name", ""),
        "email": processed_contact.get("email"),
        "company_name": processed_contact.get("company_name"),
        "company_type": processed_contact.get("company_type")
    }
    
    # Add eventtype and table if provided in input (preserve as-is)
    if eventtype is not None:
        output_data["eventtype"] = eventtype
    if table is not None:
        output_data["table"] = table
    
    # Add webhook field
    output_data["webhook"] = "bitrix"
    
    return output_data


# Direct function call - can be used by backend or run directly
if __name__ == "__main__":
    try:
        # Example: process contact with input JSON
        input_data = {
            "id": "178",
            "eventtype": "UPDATE",
            "table": "company"
        }
        output_data = process_contact_data(input_data)
        
        # Save output to file
        output_file = "output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nOutput saved to: {output_file}")
        
        # Print summary
        print("\n=== Summary ===")
        print(f"Contact ID: {output_data.get('id')}")
        print(f"Full Name: {output_data.get('full_name')}")
        print(f"Email: {output_data.get('email')}")
        print(f"Company Name: {output_data.get('company_name')}")
        if 'eventtype' in output_data:
            print(f"Event Type: {output_data['eventtype']}")
        if 'table' in output_data:
            print(f"Table: {output_data['table']}")
        if 'webhook' in output_data:
            print(f"Webhook: {output_data['webhook']}")
        
    except Exception as e:
        print(f"Error processing contact: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

