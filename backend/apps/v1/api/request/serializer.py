"""
Marshmallow serializers for request API responses.
"""

from datetime import datetime
from apps.v1.api.request.models.attribute import Priority
from apps.v1.api.request.models.attribute import RequestPhase
from config.env_config import get_settings
from marshmallow import INCLUDE, Schema, fields, post_dump

settings = get_settings()


class UserDetailSerializer(Schema):
    """User detail serializer for nested user_details array."""

    id = fields.Method("get_id", data_key="id", required=False, allow_none=True)
    name = fields.Method("get_name", data_key="name", required=False, allow_none=True)
    email = fields.Method("get_email", data_key="email", required=False, allow_none=True)
    role = fields.Method("get_role", data_key="role", required=False, allow_none=True)
    role_type = fields.Str(data_key="role_type", required=False, allow_none=True)

    def get_id(self, obj):
        """Get id as string."""
        if isinstance(obj, dict):
            return obj.get("id")
        if hasattr(obj, "id") and obj.id:
            return str(obj.id)
        elif hasattr(obj, "uuid") and obj.uuid:
            return str(obj.uuid)
        return None

    def get_name(self, obj):
        """Get name from dict or object."""
        if isinstance(obj, dict):
            return obj.get("name")
        return getattr(obj, "name", None)

    def get_email(self, obj):
        """Get email from dict or object."""
        if isinstance(obj, dict):
            return obj.get("email")
        return getattr(obj, "email", None)

    def get_role(self, obj):
        """Get role from dict or object."""
        if isinstance(obj, dict):
            return obj.get("role")
        # Get role from relationship
        if hasattr(obj, "role") and obj.role:
            return getattr(obj.role, "name", None)
        return None


class ProductDetailSerializer(Schema):
    """Product detail serializer for nested product_details array."""

    id = fields.Method("get_id", data_key="id", required=False, allow_none=True)
    name = fields.Method("get_name", data_key="name", required=False, allow_none=True)
    description = fields.Method(
        "get_description", data_key="description", required=False, allow_none=True
    )
    quantity = fields.Method("get_quantity", data_key="quantity", required=False, allow_none=True)
    package_size = fields.Method(
        "get_package_size", data_key="package_size", required=False, allow_none=True
    )
    target_price = fields.Method(
        "get_target_price", data_key="target_price", required=False, allow_none=True
    )
    currency_id = fields.Str(data_key="currency_id", required=False, allow_none=True)
    certificate = fields.List(
        fields.Raw(),
        data_key="certificate",
        required=False,
        allow_none=True,
        load_default=[],
    )
    status = fields.Method("get_status", data_key="status", required=False, allow_none=True)
    created_at = fields.Method(
        "get_created_at", data_key="created_at", required=False, allow_none=True
    )
    updated_at = fields.Method(
        "get_updated_at", data_key="updated_at", required=False, allow_none=True
    )

    def get_created_at(self, obj):
        """Get created_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("created_at")
        else:
            value = getattr(obj, "created_at", None) if hasattr(obj, "created_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("updated_at")
        else:
            value = getattr(obj, "updated_at", None) if hasattr(obj, "updated_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_id(self, obj):
        """Get id as string."""
        if isinstance(obj, dict):
            return obj.get("id")
        if hasattr(obj, "id") and obj.id:
            return str(obj.id)
        elif hasattr(obj, "uuid") and obj.uuid:
            return str(obj.uuid)
        return None

    def get_name(self, obj):
        """Get name from dict or object."""
        if isinstance(obj, dict):
            return obj.get("name")
        return getattr(obj, "name", None)

    def get_description(self, obj):
        """Get description from dict or object."""
        if isinstance(obj, dict):
            return obj.get("description")
        return getattr(obj, "description", None)

    def get_quantity(self, obj):
        """Get quantity from dict or object."""
        if isinstance(obj, dict):
            return obj.get("quantity")
        return getattr(obj, "quantity", None)

    def get_package_size(self, obj):
        """Get package_size from dict or object."""
        if isinstance(obj, dict):
            return obj.get("package_size")
        return getattr(obj, "package_size", None) or getattr(obj, "package_material", None)

    def get_target_price(self, obj):
        """Get target_price from dict or object."""
        if isinstance(obj, dict):
            return obj.get("target_price")
        price = getattr(obj, "target_price", None) or getattr(obj, "price", None)
        return float(price) if price else None

    def get_status(self, obj):
        """Get status from active field or dict."""
        if isinstance(obj, dict):
            return obj.get("status", "active")
        if hasattr(obj, "active"):
            return "active" if obj.active else "inactive"
        return "active"


class MailCommunicationSerializer(Schema):
    """Mail communication serializer for nested mail_communication array."""

    id = fields.Method("get_id", data_key="id", required=False, allow_none=True)
    to_person_name = fields.Method(
        "get_to_person_name", data_key="to_person_name", required=False, allow_none=True
    )
    to_person_email = fields.Method(
        "get_to_person_email",
        data_key="to_person_email",
        required=False,
        allow_none=True,
    )
    from_person_email = fields.Method(
        "get_from_person_email",
        data_key="from_person_email",
        required=False,
        allow_none=True,
    )
    subject = fields.Str(data_key="subject", required=False, allow_none=True)
    content = fields.Method("get_content", data_key="content", required=False, allow_none=True)
    mail_type = fields.Method(
        "get_mail_type", data_key="mail_type", required=False, allow_none=True
    )
    # attachments = fields.Method(
    #     "get_attachments", data_key="attachments", required=False, allow_none=True, load_default=[]
    # )
    status = fields.Str(data_key="status", required=False, allow_none=True, load_default="active")
    created_at = fields.Method(
        "get_created_at", data_key="created_at", required=False, allow_none=True
    )
    updated_at = fields.Method(
        "get_updated_at", data_key="updated_at", required=False, allow_none=True
    )
    sent_at = fields.Method("get_sent_at", data_key="sent_at", required=False, allow_none=True)
    received_at = fields.Method(
        "get_received_at", data_key="received_at", required=False, allow_none=True
    )

    def get_id(self, obj):
        """Get id as string."""
        if isinstance(obj, dict):
            return obj.get("id")
        if hasattr(obj, "id") and obj.id:
            return obj.id
        elif hasattr(obj, "uuid") and obj.uuid:
            return str(obj.uuid)
        return None

    def get_created_at(self, obj):
        """Get created_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("created_at")
        else:
            value = getattr(obj, "created_at", None) if hasattr(obj, "created_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("updated_at")
        else:
            value = getattr(obj, "updated_at", None) if hasattr(obj, "updated_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_sent_at(self, obj):
        """Get sent_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("sent_at")
        else:
            value = getattr(obj, "sent_at", None) if hasattr(obj, "sent_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_received_at(self, obj):
        """Get received_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("received_at")
        else:
            value = getattr(obj, "received_at", None) if hasattr(obj, "received_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_to_person_name(self, obj):
        """Get to person name from receiver_string or receiver_json."""
        if isinstance(obj, dict):
            return obj.get("to_person_name")
        # Try to extract from receiver_json first
        receiver_json = getattr(obj, "receiver_json", None)
        if receiver_json:
            if isinstance(receiver_json, list) and receiver_json:
                # If it's a list, try to get name from first item
                first_item = receiver_json[0]
                if isinstance(first_item, dict):
                    return first_item.get("name") or first_item.get("emailAddress", {}).get("name")
        # Fallback to receiver_string
        return getattr(obj, "receiver_string", None)

    def get_to_person_email(self, obj):
        """Get to person email from receiver_json or receiver_string."""
        if isinstance(obj, dict):
            return obj.get("to_person_email")
        receiver_json = getattr(obj, "receiver_json", None)
        if receiver_json:
            if isinstance(receiver_json, list) and receiver_json:
                first_item = receiver_json[0]
                if isinstance(first_item, dict):
                    return first_item.get("emailAddress", {}).get("address") or first_item.get(
                        "address"
                    )
                elif isinstance(first_item, str):
                    return first_item
        return getattr(obj, "receiver_string", None)

    def get_from_person_email(self, obj):
        """Get from person email from sender_email."""
        if isinstance(obj, dict):
            return obj.get("from_person_email")
        return getattr(obj, "sender_email", None)

    def get_content(self, obj):
        """Get content from content_text."""
        if isinstance(obj, dict):
            return obj.get("content")
        return getattr(obj, "content_text", None)

    def get_mail_type(self, obj):
        """Determine mail type based on received_at."""
        if isinstance(obj, dict):
            return obj.get("mail_type", "sent")
        if hasattr(obj, "received_at") and obj.received_at:
            return "received"
        return "sent"

    def get_attachments(self, obj):
        """Get attachments list."""
        if isinstance(obj, dict):
            return obj.get("attachments", [])
        if hasattr(obj, "attachments") and obj.attachments:
            return [
                {
                    "filename": getattr(a, "filename", None) or getattr(a, "name", None),
                    "url": getattr(a, "storage_path", None)
                    or getattr(a, "url", None)
                    or getattr(a, "file_path", None),
                    "size": getattr(a, "size", None) or getattr(a, "file_size", None),
                    "content_type": getattr(a, "content_type", None)
                    or getattr(a, "mime_type", None),
                }
                for a in obj.attachments
            ]
        return []


class DocumentDetailSerializer(Schema):
    """Document detail serializer for nested document_details array."""

    id = fields.Method("get_id", data_key="id", required=False, allow_none=True)
    url = fields.Method("get_url", data_key="url", required=False, allow_none=True)
    file_name = fields.Str(data_key="file_name", required=False, allow_none=True)
    file_type = fields.Str(data_key="file_type", required=False, allow_none=True)
    file_size = fields.Int(data_key="file_size", required=False, allow_none=True)
    status = fields.Str(data_key="status", required=False, allow_none=True, load_default="active")
    created_at = fields.Method(
        "get_created_at", data_key="created_at", required=False, allow_none=True
    )
    updated_at = fields.Method(
        "get_updated_at", data_key="updated_at", required=False, allow_none=True
    )

    def get_id(self, obj):
        """Get id as string."""
        if isinstance(obj, dict):
            return obj.get("id")
        if hasattr(obj, "id") and obj.id:
            return str(obj.id)
        elif hasattr(obj, "uuid") and obj.uuid:
            return str(obj.uuid)
        return None

    def get_url(self, obj):
        """Extract URL from path JSON or use url field."""
        import json

        # Try to get URL from path field (which is JSON with showUrl and downloadUrl)
        path = getattr(obj, "path", None)
        if path:
            try:
                if isinstance(path, dict):
                    path_data = path
                elif isinstance(path, str) and path.lstrip().startswith("{"):
                    path_data = json.loads(path)
                else:
                    path_data = None

                if isinstance(path_data, dict):
                    # Prefer downloadUrl, fallback to showUrl
                    url_value = path_data.get("downloadUrl") or path_data.get("showUrl")
                    if url_value:
                        return url_value
            except (json.JSONDecodeError, TypeError):
                pass

            # If path is a plain string (relative path), build full URL if base is configured
            if isinstance(path, str):
                if path.startswith("http://") or path.startswith("https://"):
                    return path
                base_url = getattr(settings, "AZURE_BLOB_STORAGE_URL", None) or ""
                if base_url:
                    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
                return path

        # Fallback to url field
        url_value = getattr(obj, "url", None)
        if url_value:
            if isinstance(url_value, dict):
                return url_value.get("downloadUrl") or url_value.get("showUrl")
            if isinstance(url_value, str):
                try:
                    url_data = json.loads(url_value)
                    if isinstance(url_data, dict):
                        return url_data.get("downloadUrl") or url_data.get("showUrl")
                except (json.JSONDecodeError, TypeError):
                    return url_value
                return url_value
        return None

    def get_created_at(self, obj):
        """Get created_at as ISO format string, handling both datetime objects and strings."""
        if hasattr(obj, "created_at") and obj.created_at:
            value = obj.created_at
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string, handling both datetime objects and strings."""
        if hasattr(obj, "updated_at") and obj.updated_at:
            value = obj.updated_at
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None


class StageTimelineSerializer(Schema):
    """Stage timeline serializer for nested stage_timeline array."""

    # stage mapping in serializer
    stage_status_mapping = {
        "new_unclear": "pending_response",
        "new_clear": "on_track",
        "continue": "on_track",
        "reject": "delayed",
        "accept": "awaiting_client",
        "approved": "followed_up_required",
    }
    id = fields.Method("get_id", data_key="id", required=False, allow_none=True)
    stage_name = fields.Str(data_key="stage_name", required=False, allow_none=True)
    stage_description = fields.Method(
        "get_stage_description",
        data_key="stage_description",
        required=False,
        allow_none=True,
    )
    stage_number = fields.Method(
        "get_stage_number", data_key="stage_number", required=False, allow_none=True
    )
    stage_status = fields.Method(
        "get_stage_status", data_key="stage_status", required=False, allow_none=True
    )
    created_at = fields.Method(
        "get_created_at", data_key="created_at", required=False, allow_none=True
    )
    updated_at = fields.Method(
        "get_updated_at", data_key="updated_at", required=False, allow_none=True
    )

    def get_created_at(self, obj):
        """Get created_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("created_at")
        else:
            value = getattr(obj, "created_at", None) if hasattr(obj, "created_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("updated_at")
        else:
            value = getattr(obj, "updated_at", None) if hasattr(obj, "updated_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_id(self, obj):
        """Get id as string."""
        if isinstance(obj, dict):
            return str(obj.get("id")) if obj.get("id") else None
        if hasattr(obj, "id") and obj.id:
            return str(obj.id)
        elif hasattr(obj, "uuid") and obj.uuid:
            return str(obj.uuid)
        return None

    def get_stage_name(self, obj):
        """Get stage_name."""
        if isinstance(obj, dict):
            return obj.get("stage_name")
        return getattr(obj, "stage_name", None)

    def get_stage_number(self, obj):
        """Get stage_number from order_sequence."""
        if isinstance(obj, dict):
            return obj.get("stage_number")
        return getattr(obj, "order_sequence", None) or getattr(obj, "stage_number", None)

    def get_stage_description(self, obj):
        """Get stage description from stage_name if stage_description doesn't exist."""
        if isinstance(obj, dict):
            return obj.get("stage_description") or obj.get("stage_name")
        if hasattr(obj, "stage_description") and obj.stage_description:
            return obj.stage_description
        return getattr(obj, "stage_name", None)

    def get_stage_status(self, obj):
        """Map stage_status value."""
        # Handle both dict and object
        if isinstance(obj, dict):
            status_value = obj.get("stage_status")
        else:
            status_value = (
                getattr(obj, "stage_status", None) if hasattr(obj, "stage_status") else None
            )

        if status_value:
            # Handle enum objects
            if hasattr(status_value, "value"):
                status_str = str(status_value.value).lower()
            else:
                status_str = str(status_value).lower()
            # Map using the mapping, or return as-is if not in mapping
            mapped = self.stage_status_mapping.get(status_str)
            return mapped if mapped else status_str
        return None

    @post_dump
    def convert_datetime_to_string(self, data, **kwargs):
        """Convert datetime objects to ISO format strings for JSON serialization."""
        for field in ["created_at", "updated_at"]:
            if field in data and data[field]:
                value = data[field]
                if isinstance(value, datetime):
                    data[field] = value.isoformat()
        return data


class RequestDetailSerializer(Schema):
    """
    Request detail serializer for GET /v1/request/{id}/ endpoint.

    Serializes request data according to the API specification in plan.md.
    """

    id = fields.Integer(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    phase = fields.Str(data_key="phase", required=True)
    request_id = fields.Str(data_key="request_id", required=True)
    customer_company_name = fields.Str(data_key="customer_company_name", required=True)
    customer_email = fields.Str(data_key="customer_email", required=True)
    customer_country = fields.Str(data_key="customer_country", required=True)
    customer_full_name = fields.Str(data_key="customer_full_name", required=True)
    # priority shouble a convert to capitalize
    priority = fields.Method(
        "get_priority",
        data_key="priority",
        required=False,
        allow_none=True,
    )
    bitrix_url = fields.Str(data_key="bitrix_url", required=False, allow_none=True)
    bitrix_id = fields.Int(data_key="bitrix_id", required=False, allow_none=True)
    company_name = fields.Str(data_key="company_name", required=False, allow_none=True)
    group_name = fields.Str(data_key="group_name", required=False, allow_none=True)
    prodcut_category = fields.Str(data_key="prodcut_category", required=False, allow_none=True)
    status = fields.Str(data_key="status", required=True)
    created_at = fields.Method("get_created_at", data_key="created_at", required=True)
    updated_at = fields.Method("get_updated_at", data_key="updated_at", required=True)
    last_contact = fields.Method(
        "get_last_contact", data_key="last_contact", required=False, allow_none=True
    )
    etd = fields.Method("get_etd", data_key="etd", required=False, allow_none=True)
    destination_country = fields.Str(
        data_key="destination_country", required=False, allow_none=True
    )

    def get_id(self, obj):
        """Get id as string."""
        if isinstance(obj, dict):
            return obj.get("id")
        if hasattr(obj, "id") and obj.id:
            return str(obj.id)
        elif hasattr(obj, "uuid") and obj.uuid:
            return str(obj.uuid)
        return None

    def get_created_at(self, obj):
        """Get created_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("created_at")
        else:
            value = getattr(obj, "created_at", None) if hasattr(obj, "created_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("updated_at")
        else:
            value = getattr(obj, "updated_at", None) if hasattr(obj, "updated_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_last_contact(self, obj):
        """Get last_contact as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("last_contact")
        else:
            value = getattr(obj, "last_contact", None) if hasattr(obj, "last_contact") else None
        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_etd(self, obj):
        """Get etd as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("etd")
        else:
            value = getattr(obj, "etd", None) if hasattr(obj, "etd") else None
        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_priority(self, obj):
        """Get priority as capitalized string."""
        if isinstance(obj, dict):
            value = obj.get("priority")
        else:
            value = getattr(obj, "priority", None)

        if value is None:
            return None

        if hasattr(value, "name"):
            return value.name.capitalize()

        if isinstance(value, str):
            return value.capitalize()

        return str(value).capitalize()

    user_details = fields.List(
        fields.Nested(UserDetailSerializer),
        data_key="user_details",
        required=False,
        allow_none=True,
        load_default=[],
    )
    product_details = fields.List(
        fields.Nested(ProductDetailSerializer),
        data_key="product_details",
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
    stage_timeline = fields.List(
        fields.Nested(StageTimelineSerializer),
        data_key="stage_timeline",
        required=False,
        allow_none=True,
        load_default=[],
    )

    @post_dump
    def ensure_datetime_strings(self, data, **kwargs):
        """Ensure all datetime objects in nested data are converted to strings."""

        def convert_datetime_recursive(obj):
            """Recursively convert datetime objects to ISO format strings."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime_recursive(item) for item in obj]
            return obj

        return convert_datetime_recursive(data)


class RequestListItemSerializer(Schema):
    """
    Request list item serializer for GET /v1/request/list/ endpoint.

    Serializes individual request items in the list response.
    """

    id = fields.Method("get_id", data_key="id", required=True)
    name = fields.Str(data_key="name", required=False, allow_none=True)
    phase = fields.Str(data_key="phase", required=False, allow_none=True)
    request_id = fields.Str(data_key="request_id", required=False, allow_none=True)
    customer_company_name = fields.Str(
        data_key="customer_company_name", required=False, allow_none=True
    )
    customer_email = fields.Str(data_key="customer_email", required=False, allow_none=True)
    customer_country = fields.Str(data_key="customer_country", required=False, allow_none=True)
    customer_full_name = fields.Str(data_key="customer_full_name", required=False, allow_none=True)
    priority = fields.Method("get_priority", data_key="priority", required=False, allow_none=True)
    bitrix_url = fields.Str(data_key="bitrix_url", required=False, allow_none=True)
    bitrix_id = fields.Method(
        "get_bitrix_id", data_key="bitrix_id", required=False, allow_none=True
    )
    product_category = fields.Str(data_key="product_category", required=False, allow_none=True)
    status = fields.Str(data_key="status", required=False, allow_none=True)
    created_at = fields.Method(
        "get_created_at", data_key="created_at", required=False, allow_none=True
    )
    updated_at = fields.Method(
        "get_updated_at", data_key="updated_at", required=False, allow_none=True
    )
    stage_name = fields.Str(data_key="stage_name", required=False, allow_none=True)
    assigned_to = fields.Str(data_key="assigned_to", required=False, allow_none=True)

    def get_id(self, obj):
        """Get id as string."""
        if isinstance(obj, dict):
            return obj.get("id")
        if hasattr(obj, "id") and obj.id:
            return str(obj.id)
        elif hasattr(obj, "uuid") and obj.uuid:
            return str(obj.uuid)
        return None

    def get_bitrix_id(self, obj):
        """Get bitrix_id as string."""
        if isinstance(obj, dict):
            bitrix_id = obj.get("bitrix_id")
            return str(bitrix_id) if bitrix_id else None
        if hasattr(obj, "bitrix_id") and obj.bitrix_id:
            return str(obj.bitrix_id)
        return None

    def get_created_at(self, obj):
        """Get created_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("created_at")
        else:
            value = getattr(obj, "created_at", None) if hasattr(obj, "created_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string, handling both datetime objects and strings."""
        if isinstance(obj, dict):
            value = obj.get("updated_at")
        else:
            value = getattr(obj, "updated_at", None) if hasattr(obj, "updated_at") else None

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_priority(self, obj):
        """Get priority as capitalized string."""
        if isinstance(obj, dict):
            return str(Priority(obj.get("priority")).name.capitalize())
        return str(Priority(obj, "priority", None).name.capitalize())


class PaginationSerializer(Schema):
    """
    Pagination metadata serializer.
    """

    page = fields.Int(data_key="page", required=True)
    limit = fields.Int(data_key="limit", required=True)
    total = fields.Int(data_key="total", required=True)
    pages = fields.Int(data_key="pages", required=True)


class RequestListDataSerializer(Schema):
    """
    Request list data serializer containing items array.
    """

    items = fields.List(
        fields.Nested(RequestListItemSerializer),
        data_key="items",
        required=True,
    )


class RequestSerializer(Schema):
    """
    Request serializer for webhook operations (insert/update).
    Handles request/deal data from Bitrix24 webhooks.
    """

    class Meta:
        unknown = INCLUDE
        render_as_key = True

    id = fields.Int(data_key="id", required=False, allow_none=True)
    bitrix_id = fields.Raw(data_key="bitrix_id", required=False, allow_none=True)
    name = fields.Str(data_key="name", required=False, allow_none=True)
    request_type = fields.Str(data_key="request_type", required=False, allow_none=True)
    deal_stage = fields.Str(data_key="deal_stage", required=False, allow_none=True)
    probability = fields.Int(data_key="probability", required=False, allow_none=True)
    currency = fields.Str(data_key="currency", required=False, allow_none=True)
    total = fields.Float(data_key="total", required=False, allow_none=True)
    is_manual_opportunity = fields.Bool(
        data_key="is_manual_opportunity", required=False, allow_none=True
    )
    tax_rate = fields.Float(data_key="tax_rate", required=False, allow_none=True)
    lead = fields.Str(data_key="lead", required=False, allow_none=True)
    company_id = fields.Int(data_key="company_id", required=False, allow_none=True)
    contact_id = fields.Int(data_key="contact_id", required=False, allow_none=True)
    estimate_id = fields.Int(data_key="estimate_id", required=False, allow_none=True)
    start_date = fields.DateTime(data_key="start_date", required=False, allow_none=True)
    end_date = fields.DateTime(data_key="end_date", required=False, allow_none=True)
    responsible_person = fields.Int(data_key="responsible_person", required=False, allow_none=True)
    created_by = fields.Int(data_key="created_by", required=False, allow_none=True)
    modified_by = fields.Int(data_key="modified_by", required=False, allow_none=True)
    available_to_everyone = fields.Bool(
        data_key="available_to_everyone", required=False, allow_none=True
    )
    opened = fields.Bool(data_key="opened", required=False, allow_none=True)
    closed = fields.Bool(data_key="closed", required=False, allow_none=True)
    comment = fields.Str(data_key="comment", required=False, allow_none=True)
    additional_information = fields.Str(
        data_key="additional_information", required=False, allow_none=True
    )
    pipeline = fields.Str(data_key="pipeline", required=False, allow_none=True)
    stage_group = fields.Str(data_key="stage_group", required=False, allow_none=True)
    observer_bitrixids = fields.Raw(data_key="observer_bitrixids", required=False, allow_none=True)


class PaginatedRequestListResponseSerializer(Schema):
    """
    Paginated request list response serializer.
    """

    status = fields.Str(data_key="status", required=True)
    pagination = fields.Nested(PaginationSerializer, data_key="pagination", required=True)
    data = fields.Nested(RequestListDataSerializer, data_key="data", required=True)
    message = fields.Str(data_key="message", required=False, allow_none=True, load_default="")


class StageListItemSerializer(Schema):
    """Serializer for stage list items in GET /v1/request/stages endpoint."""

    id = fields.Integer(data_key="id", required=True)
    stage_name = fields.Str(data_key="stage_name", required=False, allow_none=True)
    stage_number = fields.Int(data_key="stage_number", required=False, allow_none=True)
    phase = fields.Method("get_phase", data_key="phase", required=False, allow_none=True)
    order_sequence = fields.Int(data_key="order_sequence", required=False, allow_none=True)
    next_stage_id = fields.Integer(data_key="next_stage_id", required=False, allow_none=True)
    next_stage_name = fields.Method(
        "get_next_stage_name",
        data_key="next_stage_name",
        required=False,
        allow_none=True,
    )
    parent_id = fields.Integer(data_key="parent_id", required=False, allow_none=True)
    created_at = fields.Method(
        "get_created_at", data_key="created_at", required=False, allow_none=True
    )
    updated_at = fields.Method(
        "get_updated_at", data_key="updated_at", required=False, allow_none=True
    )

    def get_phase(self, obj):
        """Get phase as uppercase string (enum name)."""
        if isinstance(obj, dict):
            value = obj.get("phase")
        else:
            value = getattr(obj, "phase", None)

        if value:
            if isinstance(value, str):
                # If it's already a string, try to match enum name
                try:
                    phase_enum = RequestPhase(value.lower())
                    return phase_enum.name.upper()
                except (ValueError, AttributeError):
                    return value.upper()
            elif hasattr(value, "name"):
                # If it's an enum, return the name in uppercase
                return value.name.upper()
            elif hasattr(value, "value"):
                # Fallback to value if name doesn't exist
                return value.value.upper()
        return None

    def get_next_stage_name(self, obj):
        """Get next_stage_name from relationship."""
        if isinstance(obj, dict):
            return obj.get("next_stage_name")

        if hasattr(obj, "next_stage") and obj.next_stage:
            return getattr(obj.next_stage, "stage_name", None)
        return None

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
