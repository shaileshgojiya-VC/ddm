#!/usr/bin/env python3
"""
Script to process user data:
1. Get user ID as input
2. Call user.get to get all user data
3. Map fields using schema
4. Combine NAME and LAST_NAME into full_name
5. Return processed JSON with eventtype, table, and webhook
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
        method: API method name (e.g., 'user.get')
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


def get_user_from_crm(webhook_url: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user data from user.get
    
    Args:
        webhook_url: Bitrix webhook URL
        user_id: User ID
        
    Returns:
        User data dictionary or None if error
    """
    params = {
        "id": user_id
    }
    
    result = call_bitrix_api(webhook_url, "user.get", params)
    
    if result and 'result' in result:
        # user.get returns result as a list, get first item
        user_list = result['result']
        if isinstance(user_list, list) and len(user_list) > 0:
            return user_list[0]
        elif isinstance(user_list, dict):
            return user_list
    
    return None


def create_full_name(user_data: Dict[str, Any]) -> str:
    """
    Combine NAME, SECOND_NAME, and LAST_NAME into full_name
    
    Args:
        user_data: User data dictionary
        
    Returns:
        Combined full name string
    """
    name_parts = []
    
    if user_data.get("NAME"):
        name_parts.append(str(user_data["NAME"]).strip())
    
    if user_data.get("SECOND_NAME"):
        name_parts.append(str(user_data["SECOND_NAME"]).strip())
    
    if user_data.get("LAST_NAME"):
        name_parts.append(str(user_data["LAST_NAME"]).strip())
    
    return " ".join(name_parts) if name_parts else ""


def process_user(user_id: str, webhook_url: str) -> Dict[str, Any]:
    """
    Process user: get all data from user.get and extract required fields
    
    Args:
        user_id: User ID
        webhook_url: Bitrix webhook URL
        
    Returns:
        Dictionary with only required fields
    """
    print(f"Processing user ID: {user_id}")
    
    # Get ALL user data from user.get
    print("Fetching all user data from user.get...")
    user_data = get_user_from_crm(webhook_url, user_id)
    
    if not user_data:
        raise ValueError(f"User data not found for ID: {user_id}")
    
    print("User data retrieved successfully")
    
    # Create full_name from NAME, SECOND_NAME, and LAST_NAME
    full_name = create_full_name(user_data)
    print(f"Full name: {full_name}")
    
    # Extract required fields directly from user_data
    result = {
        "name": full_name,
        "bitrix_id": user_data.get("ID"),
        "email": user_data.get("EMAIL"),
        "joined_at": user_data.get("DATE_REGISTER"),
        "Position": user_data.get("WORK_POSITION")
    }
    
    # Add phone_number (prioritize PERSONAL_MOBILE, then PERSONAL_PHONE, then WORK_PHONE)
    phone_number = None
    if user_data.get("PERSONAL_MOBILE"):
        phone_number = user_data.get("PERSONAL_MOBILE")
    elif user_data.get("PERSONAL_PHONE"):
        phone_number = user_data.get("PERSONAL_PHONE")
    elif user_data.get("WORK_PHONE"):
        phone_number = user_data.get("WORK_PHONE")
    
    result["phone_number"] = phone_number if phone_number else None
    
    # Add location (combine city, state, country)
    location_parts = []
    city = user_data.get("PERSONAL_CITY") or user_data.get("WORK_CITY")
    state = user_data.get("PERSONAL_STATE") or user_data.get("WORK_STATE")
    country = user_data.get("PERSONAL_COUNTRY") or user_data.get("WORK_COUNTRY")
    
    if city:
        location_parts.append(str(city))
    if state:
        location_parts.append(str(state))
    if country:
        location_parts.append(str(country))
    
    result["location"] = ", ".join(location_parts) if location_parts else None
    
    # Add profile_image_url (from PERSONAL_PHOTO)
    result["profile_image_url"] = user_data.get("PERSONAL_PHOTO") or None
    
    return result


def process_user_data(input_data) -> Dict[str, Any]:
    """
    Main function to process user data - can be used by backend
    
    Args:
        input_data: Can be either:
            - User ID (string or integer): "4" or 4
            - Dictionary with structure: {"id": "4", "eventtype": "UPDATE", "table": "user"}
        
    Returns:
        Dictionary with processed user data including:
        {
            ... all user fields ...,
            "full_name": "...",
            "eventtype": "UPDATE",  # If provided in input
            "table": "user",        # If provided in input
            "webhook": "bitrix"
        }
        
    Raises:
        ValueError: If user_id is invalid or user not found
        RuntimeError: If BITRIX_WEBHOOK_URL is not configured
    """
    # Extract user_id and additional fields from input
    user_id = None
    eventtype = None
    table = None
    
    # Handle different input formats
    if isinstance(input_data, dict):
        # Input is a dictionary with id, eventtype, table
        user_id = input_data.get("id") or input_data.get("ID")
        eventtype = input_data.get("eventtype")
        table = input_data.get("table")
    else:
        # Input is just a user ID (string or integer)
        user_id = input_data
    
    # Convert user_id to string if it's an integer
    user_id = str(user_id) if user_id is not None else None
    
    # Use the BITRIX_WEBHOOK_URL defined at module level
    if not BITRIX_WEBHOOK_URL:
        raise RuntimeError(
            "BITRIX_WEBHOOK_URL is not configured. "
            "Please set it in the process_user.py file at the top."
        )
    
    if not user_id or not user_id.strip():
        raise ValueError("User ID is required")
    
    # Process user (no schema needed - we extract fields directly)
    processed_user = process_user(user_id, BITRIX_WEBHOOK_URL)
    
    # Add eventtype and table if provided in input (preserve as-is)
    if eventtype is not None:
        processed_user["eventtype"] = eventtype
    if table is not None:
        processed_user["table"] = table
    
    # Add webhook field
    processed_user["webhook"] = "bitrix"
    
    return processed_user


# Direct function call - can be used by backend or run directly
if __name__ == "__main__":
    try:
        # Example: process user with input JSON
        input_data = {
            "id": "1",
            "eventtype": "UPDATE",
            "table": "user"
        }
        output_data = process_user_data(input_data)
        
        # Save output to file
        output_file = "output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nOutput saved to: {output_file}")
        
        # Print summary
        print("\n=== Summary ===")
        print(f"Bitrix ID: {output_data.get('bitrix_id')}")
        print(f"Name: {output_data.get('name')}")
        print(f"Email: {output_data.get('email')}")
        print(f"Phone Number: {output_data.get('phone_number')}")
        print(f"Location: {output_data.get('location')}")
        print(f"Profile Image URL: {output_data.get('profile_image_url')}")
        if 'eventtype' in output_data:
            print(f"Event Type: {output_data['eventtype']}")
        if 'table' in output_data:
            print(f"Table: {output_data['table']}")
        
    except Exception as e:
        print(f"Error processing user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

