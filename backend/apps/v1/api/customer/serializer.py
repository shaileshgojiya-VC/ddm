"""
Marshmallow serializers for customer/contact operations.
"""

from marshmallow import Schema, fields, INCLUDE


class ContactWebhookSerializer(Schema):
    """
    Contact serializer for webhook operations.
    Handles incoming contact data from Bitrix.
    Maps to customers table.
    """
    class Meta:
        unknown = INCLUDE  # Include unknown fields
        render_as_key = True

    id = fields.Raw(data_key="id", attribute="id", allow_none=True)
    bitrix_id = fields.Raw(data_key="ID", attribute="bitrix_id", allow_none=True)
    name = fields.Raw(data_key="full_name", attribute="name", allow_none=True)  # full_name from process_contact maps to name
    email = fields.Raw(data_key="email", attribute="email", allow_none=True)  # Will be stored in email_ids as JSON array
    company_name = fields.Raw(data_key="company_name", attribute="company_name", allow_none=True)  # May not exist in model, will be filtered
