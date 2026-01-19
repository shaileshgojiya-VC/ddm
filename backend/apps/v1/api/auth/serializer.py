"""
Marshmallow serializers for authentication.
"""

from marshmallow import Schema, fields, INCLUDE


class ModuleSerializer(Schema):
    """Module serializer - field names match dictionary keys."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    slug = fields.Str(data_key="slug", required=True)



class InquiryItemSerializer(Schema):
    """inquiry item serializer for user details response."""
    
    id = fields.Str(data_key="id", required=True)
    phase = fields.Str(
        data_key="phase",
        required=False,
        allow_none=True,
    )
    stage = fields.Str(
        data_key="stage",
        required=False,
        allow_none=True,
    )
    customer_name = fields.Str(
        data_key="customer_name",
        required=False,
        allow_none=True,
    )
    company_name = fields.Str(
        data_key="company_name",
        required=False,
        allow_none=True,
    )
class RoleSerializer(Schema):
    """Role serializer - field names match dictionary keys."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    description = fields.Str(data_key="description", required=True)
    module_list = fields.List(fields.Str(), data_key="module_list", load_default=[])
    status = fields.Str(data_key="status", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)


class RoleLoginSerializer(Schema):
    """Role serializer for login response - only essential fields."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    description = fields.Str(data_key="description", required=True)


class UserSerializer(Schema):
    """User serializer - field names match dictionary keys."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    email = fields.Email(data_key="email", required=True)
    role = fields.Nested(
        RoleLoginSerializer,
        data_key="role",
        required=False,
        allow_none=True,
    )
    status = fields.Str(data_key="status", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class AdminLoginSerializer(Schema):
    """Admin login response serializer - field names match dictionary keys."""

    access_token = fields.Str(data_key="access_token", required=True)
    refresh_token = fields.Str(data_key="refresh_token", required=True)
    token_type = fields.Str(data_key="token_type", required=True)
    expires_in = fields.Int(data_key="expires_in", required=True)
    requires_password_change = fields.Bool(
        data_key="requires_password_change",
        required=True,
    )
    user = fields.Nested(
        UserSerializer,
        data_key="user",
        required=True,
    )


class UserLoginSerializer(Schema):
    """User login response serializer - field names match dictionary keys."""

    access_token = fields.Str(data_key="access_token", required=True)
    refresh_token = fields.Str(data_key="refresh_token", required=True)
    token_type = fields.Str(data_key="token_type", required=True)
    expires_in = fields.Int(data_key="expires_in", required=True)
    requires_password_change = fields.Bool(
        data_key="requires_password_change",
        required=True,
    )
    user = fields.Nested(
        UserSerializer,
        data_key="user",
        required=True,
    )


class AdminCreateUserSerializer(Schema):
    """User Serializer for creating a new user."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    email = fields.Email(data_key="email", required=True)
    role = fields.Nested(
        RoleSerializer,
        data_key="role",
        required=True,
    )
    status = fields.Str(data_key="status", required=True)
    requires_password_change = fields.Bool(
        data_key="requires_password_change",
        required=True,
    )
    created_by = fields.Str(data_key="created_by", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)


class RoleDetailSerializer(Schema):
    """Role serializer for user details response - field names match dictionary keys."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    description = fields.Str(data_key="description", required=True)
    module_list = fields.Raw(
        data_key="module_list",
        required=False,
        allow_none=True,
        load_default=[],
    )


class UserDetailsSerializer(Schema):
    """User details serializer for GET user endpoint."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    email = fields.Email(data_key="email", required=True)
    role = fields.Nested(
        RoleDetailSerializer,
        data_key="role",
        required=True,
    )
    phone_number = fields.Str(
        data_key="phone_number",
        required=False,
        allow_none=True,
    )
    location = fields.Str(
        data_key="location",
        required=False,
        allow_none=True,
    )
    profile_image_url = fields.Str(
        data_key="profile_image_url",
        required=False,
        allow_none=True,
    )
    status = fields.Str(data_key="status", required=True)
    inquiries = fields.List(
        fields.Nested(InquiryItemSerializer),
        data_key="inquiries",
        required=False,
        allow_none=True,
        load_default=[],
    )
    parent_id = fields.Str(data_key="parent_id", required=False, allow_none=True)
    created_by = fields.Nested(UserSerializer, data_key="created_by", required=False, allow_none=True)
    joined_at = fields.DateTime(data_key="joined_at", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class ChangePasswordUserSerializer(Schema):
    """User serializer for change password response - field names match dictionary keys."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    email = fields.Email(data_key="email", required=True)
    role = fields.Nested(
        RoleDetailSerializer,
        data_key="role",
        required=True,
    )
    status = fields.Str(data_key="status", required=True)
    updated_at = fields.DateTime(
        data_key="password_changed_at",
        required=True,
    )


class ChangePasswordSerializer(Schema):
    """
    Change password response serializer.
    """

    access_token = fields.Str(data_key="access_token", required=True)
    token_type = fields.Str(data_key="token_type", required=True)
    expires_in = fields.Int(data_key="expires_in", required=True)
    requires_password_change = fields.Bool(
        data_key="requires_password_change",
        required=True,
    )
    user = fields.Nested(
        ChangePasswordUserSerializer,
        data_key="user",
        required=True,
    )


class ForgetPasswordSerializer(Schema):
    """Forget password response serializer."""

    email = fields.Email(data_key="email", required=True)
    reset_token_sent = fields.Bool(
        data_key="reset_token_sent",
        required=True,
    )
    expires_in = fields.Int(data_key="expires_in", required=True)


class UserDeleteSerializer(Schema):
    """User delete serializer for DELETE user endpoint.

    Response format:
    {
      "id": "1",
      "status": "deleted",
      "deleted_at": "2024-09-11T10:20:15"
    }
    """

    id = fields.Str(data_key="id", required=True)
    status = fields.Str(data_key="status", required=True)
    deleted_at = fields.DateTime(data_key="deleted_at", required=True)


class RoleListSerializer(Schema):
    """Role serializer for user list response - field names match dictionary keys."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    description = fields.Str(data_key="description", required=True)
    module_list = fields.List(fields.Str(), data_key="module_list", load_default=[])


class UserListItemSerializer(Schema):
    """User list item serializer for GET users list endpoint."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    email = fields.Email(data_key="email", required=True)
    role = fields.Nested(
        RoleListSerializer,
        data_key="role",
        required=True,
    )
    status = fields.Str(data_key="status", required=True)
    joined_at = fields.DateTime(data_key="joined_at", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    created_by = fields.Nested(
        UserSerializer,
        data_key="created_by",
        required=False,
        allow_none=True,
    )
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class RoleListItemSerializer(Schema):
    """Role list item serializer for GET roles list endpoint."""

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    description = fields.Str(data_key="description", required=True)
    module_list = fields.List(fields.Str(), data_key="module_list", load_default=[])
    status = fields.Str(data_key="status", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class ResetPasswordSerializer(Schema):
    """Reset password response serializer."""

    reset_token = fields.Str(data_key="reset_token", required=True)
    new_password = fields.Str(data_key="new_password", required=True)
    confirm_password = fields.Str(data_key="confirm_password", required=True)


class RefreshTokenSerializer(Schema):
    """Refresh token response serializer."""

    access_token = fields.Str(data_key="access_token", required=True)
    refresh_token = fields.Str(data_key="refresh_token", required=True)
    token_type = fields.Str(data_key="token_type", required=True)
    expires_in = fields.Int(data_key="expires_in", required=True)


class UserWebhookSerializer(Schema):
    """
    User serializer for webhook operations.
    Handles incoming user data from Bitrix.
    """
    class Meta:
        unknown = INCLUDE  # Include unknown fields
        render_as_key = True

    id = fields.Raw(data_key="id", attribute="id", allow_none=True)
    bitrix_id = fields.Raw(data_key="ID", attribute="bitrix_id", allow_none=True)
    name = fields.Raw(data_key="name", attribute="name", allow_none=True)
    email = fields.Raw(data_key="email", attribute="email", allow_none=True)
    phone_number = fields.Raw(data_key="phone_number", attribute="phone_number", allow_none=True)
    location = fields.Raw(data_key="location", attribute="location", allow_none=True)
    profile_image_url = fields.Raw(data_key="profile_image_url", attribute="profile_image_url", allow_none=True)
    joined_at = fields.Raw(data_key="joined_at", attribute="joined_at", allow_none=True)
    Position = fields.Raw(data_key="Position", attribute="Position", allow_none=True)  # WORK_POSITION from Bitrix
