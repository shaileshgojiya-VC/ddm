"""
Marshmallow serializers for API filter responses.
"""

from marshmallow import Schema, fields, post_dump


class FilterOptionSerializer(Schema):
    """
    Serializer for filter option items (label-value pairs).
    """

    label = fields.Str(required=True)
    value = fields.Raw(required=True)


class StageGroupItemSerializer(Schema):
    """
    Serializer for stage items within a group.
    """

    label = fields.Str(required=True)
    value = fields.Raw(required=True)


class StageGroupSerializer(Schema):
    """
    Serializer for stage group objects (phase-grouped stages).
    """

    group_key = fields.Str(required=True)
    group_label = fields.Str(required=True)
    order_sequence = fields.Int(required=True)
    items = fields.List(
        fields.Nested(StageGroupItemSerializer),
        required=True,
    )


class FilterFieldSerializer(Schema):
    """
    Serializer for individual filter field configuration.

    Only includes relevant fields based on filter type:
    - static/dynamic: includes options
    - dynamic (stages): includes grouped flag and groups array
    - search: includes placeholder
    - date_range: includes min_date, max_date
    """

    key = fields.Str(required=True)
    label = fields.Str(required=True)
    type = fields.Str(required=True)
    options = fields.List(
        fields.Nested(FilterOptionSerializer),
        required=False,
        allow_none=True,
    )
    grouped = fields.Bool(required=False, allow_none=True)
    groups = fields.List(
        fields.Nested(StageGroupSerializer),
        required=False,
        allow_none=True,
    )
    total_options = fields.Int(required=False, allow_none=True)
    placeholder = fields.Str(required=False, allow_none=True)
    min_date = fields.Str(required=False, allow_none=True)
    max_date = fields.Str(required=False, allow_none=True)

    @post_dump
    def remove_none_fields(self, data, **kwargs):
        """
        Remove None values from serialized output.
        This ensures only relevant fields are included per filter type.
        """
        return {key: value for key, value in data.items() if value is not None}


class InquiryFilterResponseSerializer(Schema):
    """
    Serializer for inquiry filter API response.
    """

    module = fields.Str(required=True)
    filters = fields.Dict(
        keys=fields.Str(),
        values=fields.Nested(FilterFieldSerializer),
        required=True,
    )
