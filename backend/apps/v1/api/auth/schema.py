"""
Authentication Pydantic schemas.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    """Response model for admin login."""

    access_token: str
    token_type: str = "bearer"
    required_password_change: bool = False
    user: dict  # Will be serialized by Marshmallow
    status: str
    created_at: str


class AdminCreateUser(BaseModel):
    name: str
    email: EmailStr
    role_id: str  # Accepts string but will be converted to int
    # created_by removed - comes from authenticated token


class UpdateUserRequest(BaseModel):
    """Request schema for updating user information."""

    name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


class ListUsersQueryParams(BaseModel):
    """Query parameters for listing users."""

    role_id: Optional[str] = None  # Accepts string but will be converted to int
    status: Optional[str] = None
    page: int = 1
    limit: int = 10
    search: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Request schema for changing password."""

    current_password: str
    new_password: str
    confirm_password: str


class ForgetPasswordRequest(BaseModel):
    """Request schema for forget password."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request schema for reset password."""

    reset_token: str
    new_password: str
    confirm_password: str


class RefreshTokenRequest(BaseModel):
    """Request schema for refresh token."""

    refresh_token: str


class UpdateEmailInitiateRequest(BaseModel):
    """Request schema for initiating email update."""

    new_email: EmailStr
    current_password: str


class UpdateEmailInitiateResponse(BaseModel):
    """Response after initiating email update."""

    message: str
    verification_required: bool
    pending_email: str


class VerifyNewEmailRequest(BaseModel):
    """Request schema for verifying new email via token."""

    email_token: str


class VerifyNewEmailResponse(BaseModel):
    """Response after verifying new email."""

    message: str
    confirmation_link_sent: bool
    confirmation_email: str


class ConfirmEmailUpdateRequest(BaseModel):
    """Request schema for confirming email update from old email."""

    confirmation_token: str
    current_password: str


class ConfirmEmailUpdateResponse(BaseModel):
    """Response after confirming email update."""

    message: str
    new_email: str
    updated_at: str


class UpdateProfileRequest(BaseModel):
    """Request schema for updating user profile.
    
    Only allows updating basic profile fields: name, phone_number, location.
    Does not allow: role_id, status, email, password, or other sensitive fields.
    """

    name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
