"""
Marshmallow serializers for modules.
"""

from marshmallow import Schema, fields


class ModuleListItemSerializer(Schema):
    """Module list item serializer for GET modules list endpoint."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    slug = fields.Str(data_key="slug", required=True)
    description = fields.Str(data_key="description", required=True)
    status = fields.Str(data_key="status", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)

