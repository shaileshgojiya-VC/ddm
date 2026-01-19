"""
Bitrix webhook field mapping serializer.
Maps Bitrix field names to database column names.

Multiple mapping approaches:
1. Dictionary-based mapping (current)
2. Marshmallow Schema with @pre_load hook (alternative)
3. Pattern-based automatic mapping (alternative)
"""

import re
from typing import Any, Dict, Set

from marshmallow import Schema, pre_load, INCLUDE


class BitrixFieldMappingSerializer:
    """
    Serializer for mapping Bitrix field names to database column names.
    
    Uses dictionary-based mapping for explicit control and performance.
    Alternative approaches available via class methods.
    """

    # Field mapping: Bitrix field name -> Database column name
    FIELD_MAPPING: Dict[str, str] = {
        # Address fields
        "Address_(line_2)": "address_line_2",
        "Billing_Address_(line_2)": "billing_address_line_2",
        "Street_address": "street_address",
        "Billing_Address": "billing_address",
        "Billing_City": "billing_city",
        "Billing_Zip": "billing_zip",
        "Billing_Region": "billing_region",
        "Billing_Country": "billing_country",
        "Billing_Country_Code": "billing_country_code",
        "Legal_address": "legal_address",
        "Legal_address_location_address_ID": "legal_address_location_address_id",
        "Location_address_ID": "location_address_id",
        
        # Company/Supplier fields
        "Company_Name": "company_name",
        "Company_type": "company_type",
        "Supplier_Name": "supplier_name",
        "Logo": "logo",
        
        # Boolean fields (Bitrix uses "Y"/"N", database uses True/False)
        "Has_phone": "has_phone",
        "Has_email": "has_email",
        "Has_Open_Channel": "has_open_channel",
        "Available_to_everyone": "available_to_everyone",
        "My_Company": "my_company",
        "Origin_accepted": "origin_accepted",
        
        # Other fields
        "Country_Code": "country_code",
        "Type_of_Buyer": "type_of_buyer",
        "Responsible_person": "responsible_person",
        "Created_by": "created_by",
        "Modified_by": "modified_by",
        "Created_on": "created_on",
        "Modified_on": "modified_on",
        "Last_updated_on": "last_updated_on",
        "Last_contact": "last_contact",
        "Last_timeline_activity_added_by": "last_timeline_activity_added_by",
        "Ad_system": "ad_system",
        "Ad_campaign_UTM": "ad_campaign_utm",
        "Campaign_contents": "campaign_contents",
        "Campaign_search_term": "campaign_search_term",
        "Original_version": "original_version",
        "External_source": "external_source",
        "Lost_Reason": "lost_reason",
        "Estimated_Volume": "estimated_volume",
        "Products_Manufactured": "products_manufactured",
        "annual_order_volume": "annual_order_volume",
        "Week_Commitment": "week_commitment",
        "Lead_Rank": "lead_rank",
        "New_list": "new_list",
        "New_text": "new_text",
        "Product_Category": "product_category",
        "Annual_revenue": "annual_revenue",
        "date_of_inquiry": "date_of_inquiry",
        
        # Category fields
        "CATALOG_ID": "catelog_id",
        "Catalog": "catelog_id",
        "SECTION_ID": "section_id",
        "Section": "section_id",
        "NAME": "name",
        "Name": "name",
        "CODE": "code",
        "Mnemonic_code": "code",
        "XML_ID": "external_id",  # Note: external_id may not exist in model, will be filtered
        "External_ID": "external_id",  # Note: external_id may not exist in model, will be filtered
        
        # Deal/Request fields
        "TITLE": "name",
        "TYPE_ID": "request_type",
        "Type": "request_type",
        "STAGE_ID": "deal_stage",
        "Deal_stage": "deal_stage",
        "PROBABILITY": "probability",
        "Probability": "probability",
        "CURRENCY_ID": "currency",
        "Currency": "currency",
        "OPPORTUNITY": "total",
        "Total": "total",
        "IS_MANUAL_OPPORTUNITY": "is_manual_opportunity",
        "TAX_VALUE": "tax_rate",
        "Tax_rate": "tax_rate",
        "COMPANY_ID": "company_id",
        "Company": "company_id",
        "CONTACT_ID": "contact_id",
        "Contact": "contact_id",
        "QUOTE_ID": "estimate_id",
        "Estimate": "estimate_id",
        "BEGINDATE": "start_date",
        "Start_date": "start_date",
        "CLOSEDATE": "end_date",
        "End_date": "end_date",
        "ASSIGNED_BY_ID": "responsible_person",
        "Responsible_person": "responsible_person",
        "CREATED_BY_ID": "created_by",
        "Created_by": "created_by",
        "MODIFY_BY_ID": "modified_by",
        "Modified_by": "modified_by",
        "OPENED": "opened",
        "CLOSED": "closed",
        "Closed": "closed",
        "COMMENTS": "comment",
        "Comment": "comment",
        "ADDITIONAL_INFO": "additional_information",
        "Additional_information": "additional_information",
        "CATEGORY_ID": "pipeline",
        "Pipeline": "pipeline",
        "STAGE_SEMANTIC_ID": "stage_group",
        "Stage_group": "stage_group",
        "IS_NEW": "new_deal",
        "New_deal": "new_deal",
        "IS_RECURRING": "recurring_deal",
        "Recurring_deal": "recurring_deal",
        "IS_RETURN_CUSTOMER": "repeat_deal",
        "Repeat_deal": "repeat_deal",
        "IS_REPEATED_APPROACH": "repeat_inquiry",
        "Repeat_inquiry": "repeat_inquiry",
        "SOURCE_ID": "lead_source",
        "Source": "lead_source",
        "SOURCE_DESCRIPTION": "source_information",
        "Source_information": "source_information",
        "ORIGINATOR_ID": "external_source",
        "External_source": "external_source",
        "ORIGIN_ID": "item_id_in_data_source",
        "Item_ID_in_data_source": "item_id_in_data_source",
        "LEAD_ID": "lead",
        "Lead": "lead",
        "UTM_SOURCE": "ad_system",
        "Ad_system": "ad_system",
        "UTM_MEDIUM": "medium",
        "Medium": "medium",
        "UTM_CAMPAIGN": "ad_campaign_utm",
        "Ad_campaign_UTM": "ad_campaign_utm",
        "UTM_CONTENT": "campaign_contents",
        "Campaign_contents": "campaign_contents",
        "UTM_TERM": "campaign_search_term",
        "Campaign_search_term": "campaign_search_term",
        "MOVED_BY_ID": "moved_by_id",
        "MOVED_TIME": "moved_time",
        "LAST_ACTIVITY_TIME": "last_activity_time",
        "LAST_ACTIVITY_BY": "last_activity_by",
        "LAST_COMMUNICATION_TIME": "last_communication_time",
        "REPEAT_SALE_SEGMENT_ID": "repeat_sale_segment_id",
        "DATE_CREATE": "created_at",
        "Created_on": "created_at",
        "DATE_MODIFY": "updated_at",
        "Modified_on": "updated_at",
        "observer_bitrixids": "observer_bitrixids",
        "observers": "observer_bitrixids",
        
        # User fields (from process_user.py output)
        "name": "name",  # Already processed as full_name in process_user.py
        "email": "email",
        "phone_number": "phone_number",
        "location": "location",
        "profile_image_url": "profile_image_url",
        "joined_at": "joined_at",
        "Position": "Position",  # Note: Position field may not exist in model, will be filtered
        
        # Contact fields (from process_contact.py output)
        "full_name": "name",  # full_name maps to name in customers table
        "company_name": "company_name",  # Note: company_name may not exist in model, will be filtered
    }

    # Boolean fields that need conversion from "Y"/"N" to True/False
    BOOLEAN_FIELDS: Set[str] = {
        "has_phone", "has_email", "has_open_channel", "available_to_everyone", 
        "my_company", "origin_accepted", "purchased",
        "is_manual_opportunity", "opened", "closed", "new_deal", "recurring_deal",
        "repeat_deal", "advised", "lc", "eta_required_by_client", "po2factory_customer"
    }

    # Metadata fields to skip
    METADATA_FIELDS: Set[str] = {"eventtype", "table", "webhook"}

    # No columns are excluded - all columns from the model are allowed
    # Extra columns that don't exist in the model will be handled gracefully
    EXCLUDED_COLUMNS: Set[str] = set()

    @classmethod
    def get_field_mapping(cls) -> Dict[str, str]:
        """Get the field mapping dictionary."""
        return cls.FIELD_MAPPING

    @classmethod
    def get_db_field_name(cls, bitrix_field: str) -> str:
        """
        Get database field name for a Bitrix field name.
        
        Args:
            bitrix_field: Bitrix field name
            
        Returns:
            Database column name (lowercase with underscores if no mapping exists)
        """
        # Check if there's a direct mapping
        if bitrix_field in cls.FIELD_MAPPING:
            return cls.FIELD_MAPPING[bitrix_field]
        
        # Fallback: convert to lowercase and replace spaces/underscores
        return bitrix_field.lower().replace(" ", "_").replace("(", "").replace(")", "")

    @classmethod
    def is_boolean_field(cls, db_field: str) -> bool:
        """Check if a database field is a boolean field."""
        return db_field in cls.BOOLEAN_FIELDS

    @classmethod
    def is_metadata_field(cls, field: str) -> bool:
        """Check if a field is a metadata field that should be skipped."""
        return field in cls.METADATA_FIELDS

    @classmethod
    def is_excluded_column(cls, column: str) -> bool:
        """Check if a column should be excluded."""
        return column in cls.EXCLUDED_COLUMNS

    @classmethod
    def convert_boolean_value(cls, value: Any) -> bool:
        """
        Convert Bitrix boolean value ("Y"/"N") to Python boolean.
        
        Args:
            value: Value to convert (string "Y"/"N", boolean, or other)
            
        Returns:
            Boolean value or None if value is None
        """
        if value is None:
            return None
        if isinstance(value, str):
            return value.upper() == "Y"
        if isinstance(value, bool):
            return value
        return bool(value)

    # Alternative mapping approaches
    
    @classmethod
    def normalize_field_name(cls, bitrix_field: str) -> str:
        """
        Normalize Bitrix field name to database column name using patterns.
        Alternative to explicit dictionary mapping.
        
        Patterns:
        - UPPERCASE_WITH_UNDERSCORES -> lowercase_with_underscores
        - PascalCase -> snake_case
        - "Field Name" -> field_name
        - Remove parentheses and special chars
        """
        # Check explicit mapping first
        if bitrix_field in cls.FIELD_MAPPING:
            return cls.FIELD_MAPPING[bitrix_field]
        
        # Pattern-based normalization
        normalized = bitrix_field
        
        # Remove parentheses and their contents
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        
        # Replace spaces and special chars with underscores
        normalized = re.sub(r'[^\w]+', '_', normalized)
        
        # Convert to lowercase
        normalized = normalized.lower()
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        # Handle PascalCase -> snake_case
        normalized = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', normalized).lower()
        
        return normalized

    @classmethod
    def map_fields_using_patterns(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map fields using pattern-based normalization instead of explicit dictionary.
        Useful for handling unknown/new Bitrix fields automatically.
        
        Args:
            data: Dictionary with Bitrix field names as keys
            
        Returns:
            Dictionary with database column names as keys
        """
        # Filter metadata fields
        filtered_data = {
            k: v for k, v in data.items()
            if not cls.is_metadata_field(k)
        }
        
        # Map using pattern normalization
        mapped_data = {}
        for bitrix_key, value in filtered_data.items():
            if bitrix_key == "ID":
                mapped_data["bitrix_id"] = str(value) if value else None
                continue
            
            db_key = cls.normalize_field_name(bitrix_key)
            mapped_data[db_key] = value
        
        return mapped_data

    @classmethod
    def map_fields_using_dictionary(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map fields using explicit dictionary mapping (current approach).
        More reliable for known fields, requires maintenance for new fields.
        
        Args:
            data: Dictionary with Bitrix field names as keys
            
        Returns:
            Dictionary with database column names as keys
        """
        # Filter metadata fields
        filtered_data = {
            k: v for k, v in data.items()
            if not cls.is_metadata_field(k)
        }
        
        # Map using explicit dictionary
        mapped_data = {}
        for bitrix_key, value in filtered_data.items():
            if bitrix_key == "ID":
                mapped_data["bitrix_id"] = str(value) if value else None
                continue
            
            db_key = cls.get_db_field_name(bitrix_key)
            mapped_data[db_key] = value
        
        return mapped_data


class BitrixWebhookSchema(Schema):
    """
    Marshmallow Schema for Bitrix webhook data with automatic field mapping.
    Alternative approach using Marshmallow's @pre_load hook.
    """
    
    class Meta:
        unknown = INCLUDE  # Include unknown fields
    
    @pre_load
    def map_bitrix_fields(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Pre-load hook to map Bitrix field names to database column names.
        This runs before Marshmallow processes the fields.
        """
        return BitrixFieldMappingSerializer.map_fields_using_dictionary(data)
    
    # Note: With this approach, you would define fields explicitly like:
    # name = fields.Raw(attribute="name", allow_none=True)
    # company_name = fields.Raw(attribute="company_name", allow_none=True)
    # etc.
    # But the @pre_load hook handles the mapping automatically

