#!/usr/bin/env python3
"""
Script to process deal data:
1. Get deal ID as input
2. Call crm.deal.get to get all deal data
3. Call crm.deal.productrows.get to get product IDs
4. Call crm.company.get to get company email and company type
5. Create single output.json with deal data and mapping
"""

import json
import os
import sys
import requests
from typing import Dict, Any, Optional, List

# Bitrix webhook URL - configured directly in this file
BITRIX_WEBHOOK_URL = "https://dana.bitrix24.eu/rest/218/8cxeo979k998jzqq/"

# Country list for mapping Country_of_Destination IDs to country names
COUNTRY_LIST = [
    {"ID": "130", "VALUE": "Afghanistan"},
    {"ID": "132", "VALUE": "Albania"},
    {"ID": "134", "VALUE": "Algeria"},
    {"ID": "136", "VALUE": "Andorra"},
    {"ID": "138", "VALUE": "Angola"},
    {"ID": "140", "VALUE": "Antigua and Barbuda"},
    {"ID": "142", "VALUE": "Argentina"},
    {"ID": "144", "VALUE": "Armenia"},
    {"ID": "146", "VALUE": "Australia"},
    {"ID": "148", "VALUE": "Austria"},
    {"ID": "150", "VALUE": "Azerbaijan"},
    {"ID": "152", "VALUE": "Bahamas"},
    {"ID": "154", "VALUE": "Bahrain"},
    {"ID": "156", "VALUE": "Bangladesh"},
    {"ID": "158", "VALUE": "Barbados"},
    {"ID": "160", "VALUE": "Belarus"},
    {"ID": "162", "VALUE": "Belgium"},
    {"ID": "164", "VALUE": "Belize"},
    {"ID": "166", "VALUE": "Benin"},
    {"ID": "168", "VALUE": "Bhutan"},
    {"ID": "170", "VALUE": "Bolivia"},
    {"ID": "172", "VALUE": "Bosnia and Herzegovina"},
    {"ID": "174", "VALUE": "Botswana"},
    {"ID": "176", "VALUE": "Brazil"},
    {"ID": "178", "VALUE": "Brunei"},
    {"ID": "180", "VALUE": "Bulgaria"},
    {"ID": "182", "VALUE": "Burkina Faso"},
    {"ID": "184", "VALUE": "Burundi"},
    {"ID": "186", "VALUE": "Cabo Verde"},
    {"ID": "188", "VALUE": "Cambodia"},
    {"ID": "190", "VALUE": "Cameroon"},
    {"ID": "192", "VALUE": "Canada"},
    {"ID": "194", "VALUE": "Central African Republic"},
    {"ID": "196", "VALUE": "Chad"},
    {"ID": "198", "VALUE": "Chile"},
    {"ID": "200", "VALUE": "China"},
    {"ID": "202", "VALUE": "Colombia"},
    {"ID": "204", "VALUE": "Comoros"},
    {"ID": "206", "VALUE": "Congo"},
    {"ID": "208", "VALUE": "Costa Rica"},
    {"ID": "210", "VALUE": "Ivory Coast"},
    {"ID": "212", "VALUE": "Croatia"},
    {"ID": "214", "VALUE": "Cuba"},
    {"ID": "46468", "VALUE": "Curacao"},
    {"ID": "216", "VALUE": "Cyprus"},
    {"ID": "218", "VALUE": "Czech Republic (Czechia)"},
    {"ID": "220", "VALUE": "Denmark"},
    {"ID": "222", "VALUE": "Djibouti"},
    {"ID": "224", "VALUE": "Dominica"},
    {"ID": "226", "VALUE": "Dominican Republic"},
    {"ID": "228", "VALUE": "DR Congo"},
    {"ID": "230", "VALUE": "Ecuador"},
    {"ID": "232", "VALUE": "Egypt"},
    {"ID": "234", "VALUE": "El Salvador"},
    {"ID": "236", "VALUE": "Equatorial Guinea"},
    {"ID": "238", "VALUE": "Eritrea"},
    {"ID": "240", "VALUE": "Estonia"},
    {"ID": "242", "VALUE": "Eswatini"},
    {"ID": "244", "VALUE": "Ethiopia"},
    {"ID": "246", "VALUE": "Fiji"},
    {"ID": "248", "VALUE": "Finland"},
    {"ID": "250", "VALUE": "France"},
    {"ID": "252", "VALUE": "Gabon"},
    {"ID": "254", "VALUE": "Gambia"},
    {"ID": "256", "VALUE": "Georgia"},
    {"ID": "258", "VALUE": "Germany"},
    {"ID": "260", "VALUE": "Ghana"},
    {"ID": "262", "VALUE": "Greece"},
    {"ID": "264", "VALUE": "Grenada"},
    {"ID": "266", "VALUE": "Guatemala"},
    {"ID": "268", "VALUE": "Guinea"},
    {"ID": "270", "VALUE": "Guinea-Bissau"},
    {"ID": "272", "VALUE": "Guyana"},
    {"ID": "274", "VALUE": "Haiti"},
    {"ID": "276", "VALUE": "Holy See"},
    {"ID": "278", "VALUE": "Honduras"},
    {"ID": "45924", "VALUE": "Hong Kong"},
    {"ID": "280", "VALUE": "Hungary"},
    {"ID": "282", "VALUE": "Iceland"},
    {"ID": "284", "VALUE": "India"},
    {"ID": "286", "VALUE": "Indonesia"},
    {"ID": "288", "VALUE": "Iran"},
    {"ID": "290", "VALUE": "Iraq"},
    {"ID": "292", "VALUE": "Ireland"},
    {"ID": "294", "VALUE": "Israel"},
    {"ID": "296", "VALUE": "Italy"},
    {"ID": "298", "VALUE": "Jamaica"},
    {"ID": "300", "VALUE": "Japan"},
    {"ID": "302", "VALUE": "Jordan"},
    {"ID": "304", "VALUE": "Kazakhstan"},
    {"ID": "306", "VALUE": "Kenya"},
    {"ID": "308", "VALUE": "Kiribati"},
    {"ID": "45344", "VALUE": "Kosovo"},
    {"ID": "310", "VALUE": "Kuwait"},
    {"ID": "312", "VALUE": "Kyrgyzstan"},
    {"ID": "314", "VALUE": "Laos"},
    {"ID": "316", "VALUE": "Latvia"},
    {"ID": "318", "VALUE": "Lebanon"},
    {"ID": "320", "VALUE": "Lesotho"},
    {"ID": "322", "VALUE": "Liberia"},
    {"ID": "324", "VALUE": "Libya"},
    {"ID": "326", "VALUE": "Liechtenstein"},
    {"ID": "328", "VALUE": "Lithuania"},
    {"ID": "330", "VALUE": "Luxembourg"},
    {"ID": "332", "VALUE": "Madagascar"},
    {"ID": "334", "VALUE": "Malawi"},
    {"ID": "336", "VALUE": "Malaysia"},
    {"ID": "338", "VALUE": "Maldives"},
    {"ID": "340", "VALUE": "Mali"},
    {"ID": "342", "VALUE": "Malta"},
    {"ID": "344", "VALUE": "Marshall Islands"},
    {"ID": "46948", "VALUE": "Martinique"},
    {"ID": "346", "VALUE": "Mauritania"},
    {"ID": "348", "VALUE": "Mauritius"},
    {"ID": "46578", "VALUE": "Mayotte"},
    {"ID": "350", "VALUE": "Mexico"},
    {"ID": "352", "VALUE": "Micronesia"},
    {"ID": "354", "VALUE": "Moldova"},
    {"ID": "356", "VALUE": "Monaco"},
    {"ID": "358", "VALUE": "Mongolia"},
    {"ID": "360", "VALUE": "Montenegro"},
    {"ID": "362", "VALUE": "Morocco"},
    {"ID": "364", "VALUE": "Mozambique"},
    {"ID": "366", "VALUE": "Myanmar"},
    {"ID": "368", "VALUE": "Namibia"},
    {"ID": "370", "VALUE": "Nauru"},
    {"ID": "372", "VALUE": "Nepal"},
    {"ID": "374", "VALUE": "Netherlands"},
    {"ID": "376", "VALUE": "New Zealand"},
    {"ID": "378", "VALUE": "Nicaragua"},
    {"ID": "380", "VALUE": "Niger"},
    {"ID": "382", "VALUE": "Nigeria"},
    {"ID": "384", "VALUE": "North Korea"},
    {"ID": "386", "VALUE": "North Macedonia"},
    {"ID": "388", "VALUE": "Norway"},
    {"ID": "390", "VALUE": "Oman"},
    {"ID": "392", "VALUE": "Pakistan"},
    {"ID": "394", "VALUE": "Palau"},
    {"ID": "396", "VALUE": "Panama"},
    {"ID": "398", "VALUE": "Papua New Guinea"},
    {"ID": "400", "VALUE": "Paraguay"},
    {"ID": "402", "VALUE": "Peru"},
    {"ID": "404", "VALUE": "Philippines"},
    {"ID": "406", "VALUE": "Poland"},
    {"ID": "408", "VALUE": "Portugal"},
    {"ID": "44884", "VALUE": "Puerto Rico"},
    {"ID": "410", "VALUE": "Qatar"},
    {"ID": "412", "VALUE": "Romania"},
    {"ID": "414", "VALUE": "Russia"},
    {"ID": "416", "VALUE": "Rwanda"},
    {"ID": "418", "VALUE": "Saint Kitts & Nevis"},
    {"ID": "420", "VALUE": "Saint Lucia"},
    {"ID": "422", "VALUE": "Samoa"},
    {"ID": "424", "VALUE": "San Marino"},
    {"ID": "426", "VALUE": "Sao Tome & Principe"},
    {"ID": "428", "VALUE": "Saudi Arabia"},
    {"ID": "430", "VALUE": "Senegal"},
    {"ID": "432", "VALUE": "Serbia"},
    {"ID": "434", "VALUE": "Seychelles"},
    {"ID": "436", "VALUE": "Sierra Leone"},
    {"ID": "438", "VALUE": "Singapore"},
    {"ID": "440", "VALUE": "Slovakia"},
    {"ID": "442", "VALUE": "Slovenia"},
    {"ID": "444", "VALUE": "Solomon Islands"},
    {"ID": "446", "VALUE": "Somalia"},
    {"ID": "448", "VALUE": "South Africa"},
    {"ID": "450", "VALUE": "South Korea"},
    {"ID": "452", "VALUE": "South Sudan"},
    {"ID": "454", "VALUE": "Spain"},
    {"ID": "456", "VALUE": "Sri Lanka"},
    {"ID": "458", "VALUE": "St. Vincent & Grenadines"},
    {"ID": "460", "VALUE": "State of Palestine"},
    {"ID": "462", "VALUE": "Sudan"},
    {"ID": "464", "VALUE": "Suriname"},
    {"ID": "466", "VALUE": "Sweden"},
    {"ID": "468", "VALUE": "Switzerland"},
    {"ID": "470", "VALUE": "Syria"},
    {"ID": "46472", "VALUE": "Taiwan"},
    {"ID": "472", "VALUE": "Tajikistan"},
    {"ID": "474", "VALUE": "Tanzania"},
    {"ID": "476", "VALUE": "Thailand"},
    {"ID": "478", "VALUE": "Timor-Leste"},
    {"ID": "480", "VALUE": "Togo"},
    {"ID": "482", "VALUE": "Tonga"},
    {"ID": "484", "VALUE": "Trinidad and Tobago"},
    {"ID": "486", "VALUE": "Tunisia"},
    {"ID": "488", "VALUE": "Turkey"},
    {"ID": "490", "VALUE": "Turkmenistan"},
    {"ID": "46452", "VALUE": "Turks and Caicos Islands"},
    {"ID": "492", "VALUE": "Tuvalu"},
    {"ID": "494", "VALUE": "Uganda"},
    {"ID": "496", "VALUE": "Ukraine"},
    {"ID": "498", "VALUE": "United Arab Emirates"},
    {"ID": "502", "VALUE": "United States"},
    {"ID": "500", "VALUE": "United Kingdom"},
    {"ID": "504", "VALUE": "Uruguay"},
    {"ID": "506", "VALUE": "Uzbekistan"},
    {"ID": "508", "VALUE": "Vanuatu"},
    {"ID": "510", "VALUE": "Venezuela"},
    {"ID": "512", "VALUE": "Vietnam"},
    {"ID": "514", "VALUE": "Yemen"},
    {"ID": "516", "VALUE": "Zambia"},
    {"ID": "518", "VALUE": "Zimbabwe"}
]

# Create a dictionary for quick lookup: ID -> VALUE
COUNTRY_MAP = {country["ID"]: country["VALUE"] for country in COUNTRY_LIST}


def map_country_id_to_name(country_value: Any) -> Any:
    """
    Map country ID to country name using the country list
    
    Args:
        country_value: Country ID (string or number) or list of IDs, or already a name
        
    Returns:
        Country name(s) or original value if not found in map
    """
    if country_value is None:
        return None
    
    # If it's a list, map each item
    if isinstance(country_value, list):
        mapped_list = []
        for item in country_value:
            mapped_item = map_country_id_to_name(item)
            mapped_list.append(mapped_item)
        return mapped_list
    
    # Convert to string for lookup
    country_id = str(country_value).strip()
    
    # Check if it's already a country name (not a numeric ID)
    if not country_id.isdigit():
        # Might already be a name, return as is
        return country_value
    
    # Look up in the country map
    if country_id in COUNTRY_MAP:
        return COUNTRY_MAP[country_id]
    
    # If not found, return original value
    return country_value


def call_bitrix_api(webhook_url: str, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Call Bitrix API method
    
    Args:
        webhook_url: Bitrix webhook URL
        method: API method name (e.g., 'crm.deal.get')
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
        # For filter parameters with brackets like filter[PARENT_ID_2], we need to use GET
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


def get_deal_from_crm(webhook_url: str, deal_id: str) -> Optional[Dict[str, Any]]:
    """
    Get all deal data from crm.deal.get
    
    Args:
        webhook_url: Bitrix webhook URL
        deal_id: Deal ID
        
    Returns:
        Deal data dictionary or None if error
    """
    params = {
        "id": deal_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.deal.get", params)
    
    if result and 'result' in result:
        return result['result']
    
    return None


def get_deal_documents(webhook_url: str, deal_id: str) -> List[Dict[str, str]]:
    """
    Get documents linked to a deal using crm.item.list
    
    Args:
        webhook_url: Bitrix webhook URL
        deal_id: Deal ID (used as PARENT_ID_2 filter)
        
    Returns:
        List of dictionaries with title and url from urlMachine
    """
    # Bitrix API requires filter parameters in format: filter[PARENT_ID_2]
    # We need to construct the URL manually or use a different approach
    params = {
        "entityTypeId": 189,  # 189 is for documents
        "filter[PARENT_ID_2]": deal_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.item.list", params)
    
    documents = []
    if result and 'result' in result:
        result_data = result['result']
        # Handle nested 'items' key if present
        items = None
        if isinstance(result_data, dict):
            items = result_data.get('items', [])
        elif isinstance(result_data, list):
            items = result_data
        
        if isinstance(items, list):
            for item in items:
                title = item.get("title", "")
                # Get urlMachine from ufCrm8_1642626460 field (or check other possible fields)
                url = None
                
                # Check ufCrm8_1642626460 field which contains file info
                file_field = item.get("ufCrm8_1642626460")
                if file_field:
                    if isinstance(file_field, list) and len(file_field) > 0:
                        # Get first file's urlMachine
                        first_file = file_field[0]
                        if isinstance(first_file, dict):
                            url = first_file.get("urlMachine") or first_file.get("url")
                    elif isinstance(file_field, dict):
                        url = file_field.get("urlMachine") or file_field.get("url")
                
                # Always add document if title exists (even if url is None)
                if title:
                    documents.append({
                        "title": title,
                        "url": url if url else ""
                    })
    
    return documents


def get_deal_product_ids(webhook_url: str, deal_id: str) -> List[str]:
    """
    Get product IDs linked to a deal
    
    Args:
        webhook_url: Bitrix webhook URL
        deal_id: Deal ID
        
    Returns:
        List of product IDs
    """
    params = {
        "id": deal_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.deal.productrows.get", params)
    
    product_ids = []
    if result and 'result' in result:
        product_rows = result['result']
        if isinstance(product_rows, list):
            for row in product_rows:
                if 'PRODUCT_ID' in row:
                    product_ids.append(str(row['PRODUCT_ID']))
        elif isinstance(product_rows, dict):
            # Sometimes API returns dict with product rows
            for key, row in product_rows.items():
                if isinstance(row, dict) and 'PRODUCT_ID' in row:
                    product_ids.append(str(row['PRODUCT_ID']))
    
    return product_ids


def get_company_data(webhook_url: str, company_id: str) -> Dict[str, Any]:
    """
    Get company data including email and company type
    
    Args:
        webhook_url: Bitrix webhook URL
        company_id: Company ID
        
    Returns:
        Dictionary with emails (list) and company_type
    """
    if not company_id:
        return {"emails": [], "company_type": None}
    
    params = {
        "id": company_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.company.get", params)
    
    emails = []
    company_type = None
    
    if result and 'result' in result:
        company_data = result['result']
        
        # Get company type
        company_type = company_data.get("COMPANY_TYPE")
        if company_type:
            # Handle if it's a dict with ID or VALUE
            if isinstance(company_type, dict):
                company_type = company_type.get("ID") or company_type.get("VALUE") or str(company_type)
            else:
                company_type = str(company_type)
        
        # Get emails (can be multiple) - check EMAIL field first
        email = company_data.get("EMAIL")
        if email:
            # Handle list format [{"ID": "33292", "VALUE_TYPE": "WORK", "VALUE": "email@example.com", "TYPE_ID": "EMAIL"}]
            if isinstance(email, list):
                for e in email:
                    if isinstance(e, dict):
                        email_value = e.get("VALUE")
                        if email_value:
                            emails.append(str(email_value))
                    else:
                        emails.append(str(e))
            elif isinstance(email, dict):
                email_value = email.get("VALUE")
                if email_value:
                    emails.append(str(email_value))
            else:
                emails.append(str(email))
        
        # If no emails found, try alternative field names
        if not emails:
            email = company_data.get("EMAIL_VALUE") or company_data.get("EMAIL_WORK")
            if email:
                if isinstance(email, list):
                    for e in email:
                        if isinstance(e, dict):
                            email_value = e.get("VALUE")
                            if email_value:
                                emails.append(str(email_value))
                        else:
                            emails.append(str(e))
                elif isinstance(email, dict):
                    email_value = email.get("VALUE")
                    if email_value:
                        emails.append(str(email_value))
                else:
                    emails.append(str(email))
    
    return {
        "emails": emails,
        "company_type": company_type
    }


def get_contact_email(webhook_url: str, contact_id: str) -> List[str]:
    """
    Get email from contact
    
    Args:
        webhook_url: Bitrix webhook URL
        contact_id: Contact ID
        
    Returns:
        List of email addresses
    """
    if not contact_id:
        return []
    
    params = {
        "id": contact_id
    }
    
    result = call_bitrix_api(webhook_url, "crm.contact.get", params)
    
    emails = []
    if result and 'result' in result:
        contact_data = result['result']
        # Get emails - check EMAIL field first
        email = contact_data.get("EMAIL")
        if email:
            # Handle list format [{"ID": "33292", "VALUE_TYPE": "WORK", "VALUE": "email@example.com", "TYPE_ID": "EMAIL"}]
            if isinstance(email, list):
                for e in email:
                    if isinstance(e, dict):
                        email_value = e.get("VALUE")
                        if email_value:
                            emails.append(str(email_value))
                    else:
                        emails.append(str(e))
            elif isinstance(email, dict):
                email_value = email.get("VALUE")
                if email_value:
                    emails.append(str(email_value))
            else:
                emails.append(str(email))
        
        # If no emails found, try alternative field names
        if not emails:
            email = contact_data.get("EMAIL_VALUE") or contact_data.get("EMAIL_WORK")
            if email:
                if isinstance(email, list):
                    for e in email:
                        if isinstance(e, dict):
                            email_value = e.get("VALUE")
                            if email_value:
                                emails.append(str(email_value))
                        else:
                            emails.append(str(e))
                elif isinstance(email, dict):
                    email_value = email.get("VALUE")
                    if email_value:
                        emails.append(str(email_value))
                else:
                    emails.append(str(email))
    
    return emails


def get_deal_observers(webhook_url: str, deal_id: str, deal_data: Dict[str, Any]) -> List[str]:
    """
    Get observers for a deal
    First checks deal data from crm.deal.get, then tries crm.item.get
    
    Args:
        webhook_url: Bitrix webhook URL
        deal_id: Deal ID
        deal_data: Deal data from crm.deal.get
        
    Returns:
        List of observer IDs
    """
    observers = []
    
    # First, check if observers are already in the deal data from crm.deal.get
    # Check all possible field names (case-insensitive check)
    obs = None
    for key in deal_data.keys():
        if key.upper() in ['OBSERVER_IDS', 'OBSERVERS', 'UF_OBSERVERS'] or key.lower() == 'observers':
            obs = deal_data.get(key)
            if obs:
                break
    
    if obs:
        if isinstance(obs, list):
            observers = [str(o) for o in obs if o]
        elif isinstance(obs, str):
            # Handle comma-separated string
            observers = [str(o.strip()) for o in obs.split(",") if o.strip()]
        else:
            observers = [str(obs)]
        print(f"Found observers in deal data: {observers}")
    
    # If not found in deal data, try crm.item.get
    if not observers:
        params = {
            "entityTypeId": 2,  # 2 is for Deal
            "id": deal_id
        }
        
        result = call_bitrix_api(webhook_url, "crm.item.get", params)
        
        if result and 'result' in result:
            result_data = result['result']
            # Handle nested 'item' key if present
            item_data = result_data.get('item', result_data) if isinstance(result_data, dict) else result_data
            
            # Try different observer field names (check all keys case-insensitively)
            obs = None
            for key in item_data.keys() if isinstance(item_data, dict) else []:
                if key.upper() in ['OBSERVER_IDS', 'OBSERVERS', 'UF_OBSERVERS'] or key.lower() == 'observers':
                    obs = item_data.get(key)
                    if obs:
                        break
            
            if obs:
                if isinstance(obs, list):
                    observers = [str(o) for o in obs if o]
                elif isinstance(obs, str):
                    # Handle comma-separated string
                    observers = [str(o.strip()) for o in obs.split(",") if o.strip()]
                else:
                    observers = [str(obs)]
                print(f"Found observers from crm.item.get: {observers}")
    
    return observers


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


def rename_deal_fields(mapped_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rename specific deal fields to standardized names
    
    Args:
        mapped_data: Mapped deal data
        
    Returns:
        Deal data with renamed fields
    """
    # Field rename mapping: old_name -> new_name
    field_renames = {
        "Type": "request_type",
        "Company": "company_id",
        "Contact": "contact_id",
        "Estimate": "estimate_id",
        "Created_on": "created_at",
        "Modified_on": "updated_at",
        "Client_PO_/_Reference_No.": "client_reference_number",
        "#TAG": "hashtag",
        "Postscript_(PI_Additional_Details)": "postscript",
        "REF": "ref_code",  # Keep as "ref" since user didn't specify what to rename it to
        "Shipment_Date": "shipping_date",
        "Advance_Payment_%_(0_-_100)": "advance_payment",
        "Type_of_Buyer": "buyer_type",
        "Date_of_Inquiry_(inquiry_date_/_cold_contact_date)": "inquiry_date",
        "Manufacturer_Payment_Terms": "manufacturer_payment_term",
        "Next_Lots'_Loading_Dates": "next_lots_loading_dates",
        "observers": "observer_bitrixids"
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


def map_deal_fields(deal_data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map deal fields using the schema and create readable field names
    Uses listLabel if available, otherwise uses title
    Replaces PROPERTY_* fields with readable names (no duplication)
    Keeps all UF_CRM_* fields (mapped if in schema, original name if not)
    
    Args:
        deal_data: Original deal data
        schema: Schema with field definitions
        
    Returns:
        Mapped deal data with readable field names (PROPERTY_* fields replaced)
    """
    mapped_data = {}
    schema_result = schema.get("result", {})
    mapped_uf_fields = set()  # Track which UF_CRM_* fields we've mapped
    mapped_standard_fields = set()  # Track which standard fields we've mapped
    
    # Map all fields from schema (standard, PROPERTY_*, and UF_CRM_*)
    for schema_key, field_info in schema_result.items():
        # Get readable name: prioritize listLabel, then formLabel, then title
        field_label = field_info.get("listLabel", "").strip()
        if not field_label:
            # Check formLabel for fields like UF_CRM_63356ED108CB2
            field_label = field_info.get("formLabel", "").strip()
        if not field_label:
            field_label = field_info.get("title", "").strip()
        
        if field_label:
            # Convert "Field Name" -> "Field_Name"
            # For "PO2Factory-Customer", keep the hyphen (don't replace with underscore)
            readable_name = field_label.replace(" ", "_")
        else:
            readable_name = schema_key  # Keep original if no label
        
        # Extract value from field if it exists in deal_data
        if schema_key in deal_data:
            extracted_value = extract_property_value(deal_data[schema_key])
            
            if schema_key.startswith("PROPERTY_"):
                # Map PROPERTY_* fields with readable name (replace original)
                mapped_data[readable_name] = extracted_value
            elif schema_key.startswith("UF_CRM_"):
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
    for key, value in deal_data.items():
        if not key.startswith("PROPERTY_") and not key.startswith("UF_CRM_"):
            if key not in mapped_standard_fields:
                mapped_data[key] = value
    
    # Add any UF_CRM_* fields that weren't in the schema (keep original names)
    for key, value in deal_data.items():
        if key.startswith("UF_CRM_") and key not in mapped_uf_fields:
            # Keep the original UF_CRM_* field name if not in schema
            mapped_data[key] = value
    
    return mapped_data


def process_deal(deal_id: str, webhook_url: str, schema: Dict[str, Any]) -> tuple:
    """
    Process deal: get all data from crm.deal.get, get products, company info, and map fields
    
    Args:
        deal_id: Deal ID
        webhook_url: Bitrix webhook URL
        schema: Deal schema JSON
        
    Returns:
        Tuple: (mapped_deal_data, product_ids, company_id, company_info)
    """
    print(f"Processing deal ID: {deal_id}")
    
    # Get ALL deal data from crm.deal.get
    print("Fetching all deal data from crm.deal.get...")
    deal_data = get_deal_from_crm(webhook_url, deal_id)
    
    if not deal_data:
        raise ValueError(f"Deal data not found for ID: {deal_id}")
    
    print("Deal data retrieved successfully")
    
    # Get product IDs
    print("Fetching product IDs from crm.deal.productrows.get...")
    product_ids = get_deal_product_ids(webhook_url, deal_id)
    print(f"Found {len(product_ids)} product(s): {product_ids}")
    
    # Get documents
    print("Fetching documents from crm.item.list...")
    documents = get_deal_documents(webhook_url, deal_id)
    print(f"Found {len(documents)} document(s)")
    
    # Get company data (email and type)
    company_id = deal_data.get("COMPANY_ID")
    contact_id = deal_data.get("CONTACT_ID")
    company_info = {"emails": [], "company_type": None}
    
    # First, try to get email from company
    if company_id:
        print(f"Fetching company data for company ID: {company_id}")
        company_info = get_company_data(webhook_url, str(company_id))
        print(f"Company emails: {company_info['emails']}")
        print(f"Company type: {company_info['company_type']}")
    
    # If no email found in company, try contact
    if not company_info["emails"] and contact_id:
        print(f"No email found in company, trying contact ID: {contact_id}")
        contact_emails = get_contact_email(webhook_url, str(contact_id))
        if contact_emails:
            company_info["emails"] = contact_emails
            print(f"Contact emails: {contact_emails}")
        else:
            print(f"No email found in contact ID: {contact_id}")
    
    # Also check CONTACT_IDS if available (multiple contacts)
    if not company_info["emails"] and deal_data.get("CONTACT_IDS"):
        contact_ids = deal_data.get("CONTACT_IDS", [])
        if isinstance(contact_ids, list):
            for cid in contact_ids:
                contact_emails = get_contact_email(webhook_url, str(cid))
                if contact_emails:
                    company_info["emails"] = contact_emails
                    print(f"Found email from contact ID {cid}: {contact_emails}")
                    break
    
    # If still no email found after all attempts
    if not company_info["emails"]:
        print("Warning: No email found in company, contact, or CONTACT_IDS. company_email will be empty list []")
    
    # Get observers (check deal data first, then try crm.item.get)
    print("Fetching observers...")
    observers = get_deal_observers(webhook_url, deal_id, deal_data)
    print(f"Found {len(observers)} observer(s): {observers}")
    
    # Map fields using schema
    mapped_data = map_deal_fields(deal_data, schema)
    
    # Add observers to deal data (not in mapping)
    mapped_data["observers"] = [int(obs) for obs in observers] if observers else []
    
    # Rename specific fields to standardized names
    mapped_data = rename_deal_fields(mapped_data)
    
    # Map Country_of_Destination ID to country name
    if "Country_of_Destination" in mapped_data:
        mapped_data["Country_of_Destination"] = map_country_id_to_name(mapped_data["Country_of_Destination"])
    
    return mapped_data, product_ids, company_id, company_info, documents


def process_deal_data(input_data) -> Dict[str, Any]:
    """
    Main function to process deal data - can be used by backend
    
    Args:
        input_data: Can be either:
            - Deal ID (string or integer): "13928" or 13928
            - Dictionary with structure: {"id": "13928", "eventtype": "UPDATE", "table": "deal"}
        
    Returns:
        Dictionary with structure:
        {
            "deal": { ... all deal data ... },
            "mapping": {
                "deal_id": "123",
                "product_id": [456, 789],
                "company_id": 10,
                "company_email": ["email@example.com"],
                "company_type": "CUSTOMER"
            },
            "eventtype": "UPDATE",  # If provided in input
            "table": "deal"         # If provided in input
        }
        
    Raises:
        ValueError: If deal_id is invalid or deal not found
        RuntimeError: If BITRIX_WEBHOOK_URL is not configured
    """
    # Extract deal_id and additional fields from input
    deal_id = None
    eventtype = None
    table = None
    
    # Handle different input formats
    if isinstance(input_data, dict):
        # Input is a dictionary with id, eventtype, table
        deal_id = input_data.get("id") or input_data.get("ID")
        eventtype = input_data.get("eventtype")
        table = input_data.get("table")
    else:
        # Input is just a deal ID (string or integer)
        deal_id = input_data
    
    # Convert deal_id to string if it's an integer
    deal_id = str(deal_id) if deal_id is not None else None
    
    # Use the BITRIX_WEBHOOK_URL defined at module level
    if not BITRIX_WEBHOOK_URL:
        raise RuntimeError(
            "BITRIX_WEBHOOK_URL is not configured. "
            "Please set it in the process_deal.py file at the top."
        )
    
    if not deal_id or not deal_id.strip():
        raise ValueError("Deal ID is required")
    
    # Load schema
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(script_dir, "deal_schema.json")
    
    if os.path.exists(schema_file):
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    else:
        # Use empty schema if file doesn't exist
        print(f"Warning: Schema file '{schema_file}' not found. Using empty schema.")
        schema = {"result": {}}
    
    # Process deal
    mapped_deal_data, product_ids, company_id, company_info, documents = process_deal(
        deal_id, BITRIX_WEBHOOK_URL, schema
    )
    
    # Create mapping
    mapping = create_mapping(
        deal_id=deal_id,
        product_ids=product_ids,
        company_id=company_id,
        company_emails=company_info["emails"],
        company_type=company_info["company_type"],
        documents=documents
    )
    
    # Create single output JSON with deal and mapping
    output_data = {
        "deal": mapped_deal_data,
        "mapping": mapping,
        "webhook": "bitrix"
    }
    
    # Add eventtype and table if provided in input (preserve as-is)
    if eventtype is not None:
        output_data["eventtype"] = eventtype
    if table is not None:
        output_data["table"] = table
    
    return output_data


def create_mapping(deal_id: str, product_ids: List[str], company_id: Optional[str], 
                   company_emails: List[str], company_type: Optional[str],
                   documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Create mapping dictionary
    
    Args:
        deal_id: Deal ID
        product_ids: List of product IDs
        company_id: Company ID
        company_emails: List of company emails
        company_type: Company type
        documents: List of documents with title and url
        
    Returns:
        Mapping dictionary
    """
    return {
        "deal_id": str(deal_id),
        "product_id": [int(pid) for pid in product_ids] if product_ids else [],
        "company_id": int(company_id) if company_id else None,
        "company_email": company_emails if company_emails else [],
        "company_type": company_type,
        "documents": documents if documents else []
    }


# def main():
#     """
#     CLI entry point for processing deal data
#     """
#     # Get deal ID from command line argument or stdin
#     if len(sys.argv) > 1:
#         # Deal ID from command line argument
#         deal_id = sys.argv[1]
#     else:
#         # Read deal ID from stdin
#         print("Enter deal ID: ", end='', flush=True)
#         deal_id = sys.stdin.readline().strip()
#     
#     if not deal_id:
#         print("Error: Deal ID is required")
#         print("Usage: python process_deal.py <deal_id>")
#         print("   or: echo '123' | python process_deal.py")
#         sys.exit(1)
#     
#     # Process deal using the main function
#     try:
#         output_data = process_deal_data(deal_id)
#         
#         # Write to single output file
#         output_file = "output.json"
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(output_data, f, indent=2, ensure_ascii=False)
#         print(f"\nOutput saved to: {output_file}")
#         
#         # Print summary
#         print("\n=== Summary ===")
#         print(f"Deal ID: {deal_id}")
#         print(f"Product IDs: {output_data['mapping']['product_id']}")
#         print(f"Company ID: {output_data['mapping']['company_id']}")
#         print(f"Company Emails: {output_data['mapping']['company_email']}")
#         print(f"Company Type: {output_data['mapping']['company_type']}")
#         print(f"Observers: {output_data['deal'].get('observers', [])}")
#         
#     except Exception as e:
#         print(f"Error processing deal: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)


# Direct function call - can be used by backend or run directly
if __name__ == "__main__":
    try:
        # Example: process deal with input JSON
        input_data = {
            "id": "78",
            "eventtype": "UPDATE",
            "table": "deal"
        }
        output_data = process_deal_data(input_data)
        
        # Save output to file
        output_file = "output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nOutput saved to: {output_file}")
        
        # Print summary
        print("\n=== Summary ===")
        print(f"Deal ID: {output_data['deal'].get('ID')}")
        print(f"Product IDs: {output_data['mapping']['product_id']}")
        print(f"Company ID: {output_data['mapping']['company_id']}")
        print(f"Company Emails: {output_data['mapping']['company_email']}")
        print(f"Company Type: {output_data['mapping']['company_type']}")
        print(f"Observers: {output_data['deal'].get('observers', [])}")
        if 'eventtype' in output_data:
            print(f"Event Type: {output_data['eventtype']}")
        if 'table' in output_data:
            print(f"Table: {output_data['table']}")
        
    except Exception as e:
        print(f"Error processing deal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
