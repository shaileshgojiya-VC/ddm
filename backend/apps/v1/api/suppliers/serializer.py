"""
Single Marshmallow schema for supplier ingest (load) and response (dump).
"""

from datetime import datetime
from typing import Any, Dict

from marshmallow import Schema, fields, post_load, post_dump, INCLUDE

from core.utils.helper import TypeCoercion
from apps.v1.api.products.serializer import ProductListItemSerializer, DocumentDetailSerializer
from apps.v1.api.request.serializer import MailCommunicationSerializer


class SupplierSerializer(Schema):
    """Serializer for supplier data (ingest + response)."""

    class Meta:
        unknown = INCLUDE

    id = fields.Raw(data_key="id", attribute="id", allow_none=True)
    bitrix_id = fields.Raw(data_key="ID", attribute="bitrix_id", allow_none=True)
    company_type = fields.Raw(allow_none=True, data_key="Company type")
    company_name = fields.Raw(allow_none=True, data_key="Company Name")
    logo = fields.Raw(allow_none=True, data_key="Logo")
    lead = fields.Raw(allow_none=True, data_key="Lead")
    has_phone = fields.Raw(allow_none=True, data_key="Has phone")
    has_email = fields.Raw(allow_none=True, data_key="Has email")
    has_open_channel = fields.Raw(allow_none=True, data_key="Has Open Channel")
    responsible_person = fields.Raw(allow_none=True, data_key="Responsible person")
    created_by = fields.Raw(allow_none=True, data_key="Created by")
    modified_by = fields.Raw(allow_none=True, data_key="Modified by")
    payment_details = fields.Raw(allow_none=True, data_key="Payment details")
    industry = fields.Raw(allow_none=True, data_key="Industry")
    annual_revenue = fields.Raw(allow_none=True, data_key="Annual revenue")
    currency = fields.Raw(allow_none=True, data_key="Currency")
    employees = fields.Raw(allow_none=True, data_key="Employees")
    comment = fields.Raw(allow_none=True, data_key="Comment")
    created_on = fields.Raw(allow_none=True, data_key="Created on")
    modified_on = fields.Raw(allow_none=True, data_key="Modified on")
    available_to_everyone = fields.Raw(allow_none=True, data_key="Available to everyone")
    my_company = fields.Raw(allow_none=True, data_key="My Company")
    external_source = fields.Raw(allow_none=True, data_key="External source")
    original_version = fields.Raw(allow_none=True, data_key="Original version")
    street_address = fields.Raw(allow_none=True, data_key="Street address")
    address_line_2 = fields.Raw(allow_none=True, data_key="Address (line 2)")
    city = fields.Raw(allow_none=True, data_key="City")
    zip = fields.Raw(allow_none=True, data_key="Zip")
    region = fields.Raw(allow_none=True, data_key="Region")
    state = fields.Raw(allow_none=True, data_key="State / Province")
    country = fields.Raw(allow_none=True, data_key="Country")
    country_code = fields.Raw(allow_none=True, data_key="Country Code")
    location_address_id = fields.Raw(allow_none=True, data_key="Location address ID")
    legal_address = fields.Raw(allow_none=True, data_key="Legal address")
    billing_address = fields.Raw(allow_none=True, data_key="Billing Address")
    billing_address_line_2 = fields.Raw(allow_none=True, data_key="Billing Address (line 2)")
    billing_city = fields.Raw(allow_none=True, data_key="Billing City")
    billing_zip = fields.Raw(allow_none=True, data_key="Billing Zip")
    billing_region = fields.Raw(allow_none=True, data_key="Billing Region")
    billing_state = fields.Raw(allow_none=True, data_key="Billing State / Province")
    billing_country = fields.Raw(allow_none=True, data_key="Billing Country")
    billing_country_code = fields.Raw(allow_none=True, data_key="Billing Country Code")
    legal_address_location_address_id = fields.Raw(
        allow_none=True, data_key="Legal address location address ID"
    )
    ad_system = fields.Raw(allow_none=True, data_key="Ad system")
    medium = fields.Raw(allow_none=True, data_key="Medium")
    ad_campaign_utm = fields.Raw(allow_none=True, data_key="Ad campaign UTM")
    campaign_contents = fields.Raw(allow_none=True, data_key="Campaign contents")
    campaign_search_term = fields.Raw(allow_none=True, data_key="Campaign search term")
    last_timeline_activity_added_by = fields.Raw(
        allow_none=True, data_key="Last timeline activity added by"
    )
    last_updated_on = fields.Raw(allow_none=True, data_key="Last updated on")
    last_contact = fields.Raw(allow_none=True, data_key="Last contact")
    type_of_buyer = fields.Raw(allow_none=True, data_key="Type of Buyer")
    prefix = fields.Raw(allow_none=True, data_key="Prefix")
    certificates = fields.Raw(allow_none=True, data_key="Certificates")
    ops = fields.Raw(allow_none=True, data_key="OPS")
    health_mark = fields.Raw(allow_none=True, data_key="Health Mark")
    hashtag = fields.Raw(allow_none=True, data_key="#TAG")
    product_category = fields.Raw(allow_none=True, data_key="Product Category")
    week_commitment = fields.Raw(allow_none=True, data_key="Week Commitment")
    annual_order_volume = fields.Raw(allow_none=True, data_key="Annual Order Volume (FCLs)")
    lost_reason = fields.Raw(allow_none=True, data_key="Lost Reason")
    date_of_inquiry = fields.Raw(
        allow_none=True, data_key="Date of Inquiry (inquiry date / cold contact date)"
    )
    origin_accepted = fields.Raw(allow_none=True, data_key="Origin accepted")
    estimated_volume = fields.Raw(allow_none=True, data_key="Estimated Volume")
    purchased = fields.Raw(allow_none=True, data_key="Purchased")
    stars = fields.Raw(allow_none=True, data_key="Stars")
    projected = fields.Raw(allow_none=True, data_key="Projected")
    factory_certificates = fields.Raw(
        allow_none=True,
        data_key="Factory certificates:  a. ISO    b. HACCP    b. FSSC    c. GMP   d.\tLICENSE",
    )
    lead_rank = fields.Raw(allow_none=True, data_key="Lead Rank")
    new_list = fields.Raw(allow_none=True, data_key="New list")
    new_text = fields.Raw(allow_none=True, data_key="New text")
    products_manufactured = fields.Raw(allow_none=True, data_key="Products Manufactured")
    supplier_name = fields.Raw(allow_none=True, data_key="Supplier Name")
    email = fields.Raw(allow_none=True, data_key="E-mail")
    website = fields.Raw(allow_none=True, data_key="Website")
    phone = fields.Raw(allow_none=True, data_key="Phone")
    messenger = fields.Raw(allow_none=True, data_key="Messenger")

    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)

    @post_load
    def normalize_data(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Normalize and coerce data types for inbound payloads."""

        if isinstance(data.get("logo"), dict):
            logo_url = data["logo"].get("downloadUrl") or data["logo"].get("showUrl")
            data["logo"] = TypeCoercion.coerce_str(logo_url)

        if isinstance(data.get("country"), str) and "|" in data["country"]:
            data["country"] = TypeCoercion.coerce_str(data["country"].split("|")[0])

        if isinstance(data.get("email"), list) and len(data["email"]) > 0:
            email_value = (
                data["email"][0].get("VALUE") if isinstance(data["email"][0], dict) else None
            )
            data["email"] = TypeCoercion.coerce_str(email_value)

        if isinstance(data.get("website"), list) and len(data["website"]) > 0:
            website_value = (
                data["website"][0].get("VALUE") if isinstance(data["website"][0], dict) else None
            )
            data["website"] = TypeCoercion.coerce_str(website_value)

        if isinstance(data.get("phone"), list) and len(data["phone"]) > 0:
            phone_value = (
                data["phone"][0].get("VALUE") if isinstance(data["phone"][0], dict) else None
            )
            data["phone"] = TypeCoercion.coerce_str(phone_value)

        if isinstance(data.get("certificates"), list):
            cert_ids = [
                str(c.get("id", ""))
                for c in data["certificates"]
                if isinstance(c, dict) and c.get("id")
            ]
            data["certificates"] = ", ".join(cert_ids) if cert_ids else None

        # Coerce types
        # Booleans that often arrive as strings
        for key in (
            "has_phone",
            "has_email",
            "has_open_channel",
            "available_to_everyone",
            "my_company",
            "origin_accepted",
            "purchased",
        ):
            data[key] = TypeCoercion.coerce_bool(data.get(key))

        # Numeric fields that often arrive as strings
        for key in (
            "annual_revenue",
            "estimated_volume",
            "stars",
            "projected",
            "week_commitment",
            "annual_order_volume",
            "lead_rank",
            "location_address_id",
            "legal_address_location_address_id",
        ):
            data[key] = TypeCoercion.coerce_int(data.get(key))

        # Date/time fields
        for key in ("created_on", "modified_on", "last_updated_on", "date_of_inquiry"):
            data[key] = TypeCoercion.coerce_datetime(data.get(key))

        return data

    @post_dump
    def format_output(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Format output values for response - ensure id and bitrix_id are present."""
        # Ensure id is present (convert id to string)
        if "id" in data and data["id"] is not None:
            data["id"] = str(data["id"])
        elif "id" not in data:
            # Fallback: try to get from the object if available
            obj = kwargs.get("obj")
            if obj and hasattr(obj, "id") and obj.id is not None:
                data["id"] = str(obj.id)
            else:
                data["id"] = ""

        # Ensure bitrix_id is in output (copy from ID if exists)
        # This matches the products serializer behavior
        if "ID" in data:
            # Copy ID to bitrix_id for consistent response format
            data["bitrix_id"] = data["ID"]
        elif "bitrix_id" not in data:
            # Fallback: try to get from the object if available
            obj = kwargs.get("obj")
            if obj and hasattr(obj, "bitrix_id"):
                data["bitrix_id"] = obj.bitrix_id
            else:
                # Ensure bitrix_id is present even if None
                data["bitrix_id"] = None
        return data


class PriceHistoryDetailSerializer(Schema):
    """Price history detail serializer for nested price_history_details array."""

    id = fields.Method("get_id", data_key="id", required=False, allow_none=True)
    product_name = fields.Str(data_key="product_name", required=False, allow_none=True)
    price = fields.Float(data_key="price", required=False, allow_none=True)
    currency = fields.Str(data_key="currency", required=False, allow_none=True, load_default=None)
    effective_from = fields.Method(
        "get_effective_from", data_key="effective_from", required=False, allow_none=True
    )
    effective_to = fields.Method(
        "get_effective_to", data_key="effective_to", required=False, allow_none=True
    )

    def get_id(self, obj):
        """Get id as string."""
        if isinstance(obj, dict):
            return obj.get("id")
        if hasattr(obj, "id") and obj.id:
            return str(obj.id)
        return None

    def get_effective_from(self, obj):
        """Get effective_from as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("effective_from")
        else:
            value = getattr(obj, "effective_from", None) if hasattr(obj, "effective_from") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_effective_to(self, obj):
        """Get effective_to as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("effective_to")
        else:
            value = getattr(obj, "effective_to", None) if hasattr(obj, "effective_to") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None


class SupplierListSerializer(Schema):
    """Serializer to List the Suppliers


    Args:
        Schema (SupplierSerializer): SupplierSerializer
    """

    id = fields.Str(data_key="id", required=True)
    company_name = fields.Str(data_key="company_name", required=True)
    email = fields.Str(data_key="email", required=False, allow_none=True, load_default=None)
    phone_number = fields.Str(
        data_key="phone_number", required=False, allow_none=True, load_default=None
    )
    rating = fields.Float(data_key="rating", required=True)
    address = fields.Str(data_key="address", required=True)
    country = fields.Str(data_key="country", required=True)
    created_at = fields.Method("get_created_at", data_key="created_at", required=True)
    updated_at = fields.Method("get_updated_at", data_key="updated_at", required=True)
    last_contact = fields.Method("get_last_contact", data_key="last_contact", required=False, allow_none=True)
    prefix = fields.Str(data_key="prefix", required=False, allow_none=True, load_default=None)
    company_type = fields.Str(
        data_key="company_type", required=False, allow_none=True, load_default=None
    )
    category = fields.List(
        fields.Str(), data_key="category", required=False, allow_none=True, load_default=[]
    )
    sub_category = fields.List(
        fields.Str(), data_key="sub_category", required=False, allow_none=True, load_default=[]
    )
    child_category = fields.List(
        fields.Str(), data_key="child_category", required=False, allow_none=True, load_default=[]
    )

    def get_created_at(self, obj):
        """Get created_at as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("created_at")
        else:
            value = getattr(obj, "created_at", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("updated_at")
        else:
            value = getattr(obj, "updated_at", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_last_contact(self, obj):
        """Get last_contact as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("last_contact")
        else:
            value = getattr(obj, "last_contact", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

  


class SupplierGetSerializer(Schema):
    """Serializer to Get the Supplier

    Args:
        Schema (SupplierSerializer): SupplierSerializer
    """

    id = fields.Str(data_key="id", required=True)
    company_name = fields.Str(
        data_key="company_name", required=False, allow_none=True, load_default=""
    )
    email = fields.Str(data_key="email", required=False, allow_none=True, load_default="")
    phone_number = fields.Str(
        data_key="phone_number", required=False, allow_none=True, load_default=""
    )
    website = fields.Str(data_key="website", required=False, allow_none=True, load_default="")
    messanger_type = fields.Str(
        data_key="messanger_type", required=False, allow_none=True, load_default=""
    )
    messanger_number = fields.Str(
        data_key="messanger_number", required=False, allow_none=True, load_default=""
    )
    rating = fields.Float(data_key="rating", required=False, allow_none=True, load_default=0.0)
    address = fields.Str(data_key="address", required=False, allow_none=True, load_default="")
    country = fields.Str(data_key="country", required=False, allow_none=True, load_default="")
    responsible_person_name = fields.Str(
        data_key="responsible_person_name", required=False, allow_none=True, load_default=""
    )
    created_at = fields.Method("get_created_at", data_key="created_at", required=True)
    updated_at = fields.Method("get_updated_at", data_key="updated_at", required=True)
    updated_by = fields.Str(
        data_key="updated_by", required=False, allow_none=True, dump_default="", load_default=""
    )
    created_on = fields.Method(
        "get_created_on", data_key="created_on", required=False, allow_none=True
    )
    last_contact = fields.Method(
        "get_last_contact", data_key="last_contact", required=False, allow_none=True
    )
    prefix = fields.Str(data_key="prefix", required=False, allow_none=True, load_default="")
    company_type = fields.Str(
        data_key="company_type", required=False, allow_none=True, load_default=""
    )
    industry = fields.Str(data_key="industry", required=False, allow_none=True, load_default="")
    vat_number = fields.Str(data_key="vat_number", required=False, allow_none=True, load_default="")
    registraction_number = fields.Str(
        data_key="registraction_number", required=False, allow_none=True, load_default=""
    )
    supplier_name = fields.Str(
        data_key="supplier_name", required=False, allow_none=True, load_default=""
    )
    type_of_buyer = fields.Str(
        data_key="type_of_buyer", required=False, allow_none=True, load_default=""
    )
    category = fields.List(
        fields.Str(), data_key="category", required=False, allow_none=True, load_default=[]
    )
    sub_category = fields.List(
        fields.Str(), data_key="sub_category", required=False, allow_none=True, load_default=[]
    )
    child_category = fields.List(
        fields.Str(), data_key="child_category", required=False, allow_none=True, load_default=[]
    )
    products_manufactured = fields.Str(
        data_key="products_manufactured", required=False, allow_none=True, load_default=""
    )
    created_by = fields.Str(
        data_key="created_by", required=False, allow_none=True, dump_default="", load_default=""
    )
    assigned_by = fields.Method(
        "get_assigned_by", data_key="assigned_by", required=False, allow_none=True
    )
    generated_by = fields.Method(
        "get_generated_by", data_key="generated_by", required=False, allow_none=True
    )
    updated_by = fields.Method(
        "get_updated_by", data_key="updated_by", required=False, allow_none=True
    )

    def get_created_at(self, obj):
        """Get created_at as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("created_at")
        else:
            value = getattr(obj, "created_at", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("updated_at")
        else:
            value = getattr(obj, "updated_at", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_last_contact(self, obj):
        """Get last_contact as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("last_contact")
        else:
            value = getattr(obj, "last_contact", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_created_on(self, obj):
        """Get created_on as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("created_on")
        else:
            value = getattr(obj, "created_on", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_assigned_by(self, obj):
        """Get assigned_by user name from relationship or dict."""
        if isinstance(obj, dict):
            return obj.get("assigned_by")

        # Try to get from relationship
        if hasattr(obj, "assigned_by_user") and obj.assigned_by_user:
            return obj.assigned_by_user.name

        # Fallback to direct attribute
        if hasattr(obj, "assigned_by") and obj.assigned_by:
            return str(obj.assigned_by)

        return None

    def get_generated_by(self, obj):
        """Get generated_by user name from relationship or dict."""
        if isinstance(obj, dict):
            return obj.get("generated_by")

        # Try to get from relationship
        if hasattr(obj, "generated_by_user") and obj.generated_by_user:
            return obj.generated_by_user.name

        # Fallback to direct attribute
        if hasattr(obj, "generated_by") and obj.generated_by:
            return str(obj.generated_by)

        return None

    def get_updated_by(self, obj):
        """Get updated_by user name from relationship or dict."""
        if isinstance(obj, dict):
            return obj.get("updated_by")

        # Try to get from relationship
        if hasattr(obj, "updated_by_user") and obj.updated_by_user:
            return obj.updated_by_user.name

        # Fallback to direct attribute
        if hasattr(obj, "updated_by") and obj.updated_by:
            return str(obj.updated_by)

        return None

    product_details = fields.List(
        fields.Nested(ProductListItemSerializer),
        data_key="product_details",
        required=False,
        allow_none=True,
        load_default=[],
    )
    price_history_details = fields.List(
        fields.Nested(PriceHistoryDetailSerializer),
        data_key="price_history_details",
        required=False,
        allow_none=True,
        load_default=[],
    )
    mail_communication = fields.List(
        fields.Nested(MailCommunicationSerializer),
        data_key="mail_communication",
        required=False,
        allow_none=True,
        load_default=[],
    )
    document_details = fields.List(
        fields.Nested(DocumentDetailSerializer),
        data_key="document_details",
        required=False,
        allow_none=True,
        load_default=[],
    )

    @post_dump
    def format_datetime(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Format datetime fields to ISO format string."""
        datetime_fields = ["created_at", "updated_at", "last_contact", "created_on"]
        for field in datetime_fields:
            if field in data and data[field] and hasattr(data[field], "strftime"):
                data[field] = (
                    data[field].strftime("%Y-%m-%dT%H:%M:%S")
                    if not data[field].tzinfo
                    else data[field].strftime("%Y-%m-%dT%H:%M:%S%z")
                )
        return data


class SupplierDetailResponseSerializer(Schema):
    """
    Supplier detail response wrapper serializer for GET /v1/supplier/{supplier_id}/ endpoint.
    Wraps supplier detail with status and message.
    Can be modified independently to change response structure.
    """

    status = fields.Str(data_key="status", required=True)
    data = fields.Nested(SupplierGetSerializer, data_key="data", required=True)
    message = fields.Str(data_key="message", required=False, allow_none=True, load_default="")


class PaginationSerializer(Schema):
    """
    Pagination metadata serializer for paginated responses.
    Used in GET /v1/suppliers endpoint.
    """

    page = fields.Int(data_key="page", required=True)
    limit = fields.Int(data_key="limit", required=True)
    total = fields.Int(data_key="total", required=True)
    pages = fields.Int(data_key="pages", required=True)


class SupplierListDataSerializer(Schema):
    """
    Supplier list data serializer containing items array.
    Used in GET /v1/suppliers endpoint.
    """

    items = fields.List(
        fields.Nested(SupplierListSerializer),
        data_key="items",
        required=True,
    )


class PaginatedSupplierListResponseSerializer(Schema):
    """
    Paginated supplier list response serializer for GET /v1/suppliers endpoint.
    Wraps status, pagination metadata, data items, and message.
    """

    status = fields.Str(data_key="status", required=True)
    pagination = fields.Nested(PaginationSerializer, data_key="pagination", required=True)
    data = fields.Nested(SupplierListDataSerializer, data_key="data", required=True)
    message = fields.Str(data_key="message", required=False, allow_none=True, load_default="")
