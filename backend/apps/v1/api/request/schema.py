"""
Pydantic schemas for request API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UserDetailSchema(BaseModel):
    """User detail schema for nested user_details array."""

    uuid: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    role_type: Optional[str] = None

    class Config:
        from_attributes = True


class ProductDetailSchema(BaseModel):
    """Product detail schema for nested product_details array."""

    uuid: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    package_size: Optional[str] = None
    target_price: Optional[float] = None
    certificate: Optional[List] = []
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MailCommunicationSchema(BaseModel):
    """Mail communication schema for nested mail_communication array."""

    uuid: Optional[str] = None
    to_person_name: Optional[str] = None
    to_person_email: Optional[EmailStr] = None
    from_person_email: Optional[EmailStr] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    mail_type: Optional[str] = None
    attachments: Optional[List] = []
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentDetailSchema(BaseModel):
    """Document detail schema for nested document_details array."""

    uuid: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StageTimelineSchema(BaseModel):
    """Stage timeline schema for nested stage_timeline array."""

    uuid: Optional[str] = None
    stage_name: Optional[str] = None
    stage_description: Optional[str] = None
    stage_number: Optional[int] = None
    stage_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RequestDetailResponseSchema(BaseModel):
    """Request detail response schema for GET /v1/request/{uuid}/ endpoint."""

    uuid: str
    name: str
    phase: str
    request_id: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_country: Optional[str] = None
    priority: Optional[str] = None
    bitrix_url: Optional[str] = None
    bitrix_id: Optional[int] = None
    company_name: Optional[str] = None
    group_name: Optional[str] = None
    prodcut_category: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    user_details: List[UserDetailSchema] = []
    product_details: List[ProductDetailSchema] = []
    mail_communication: List[MailCommunicationSchema] = []
    document_details: List[DocumentDetailSchema] = []
    stage_timeline: List[StageTimelineSchema] = []

    class Config:
        from_attributes = True


class StageListItemResponseSchema(BaseModel):
    """Stage list item response schema for GET /v1/request/stages/list/ endpoint."""

    id: int
    stage_name: str
    stage_description: str
    stage_number: int
    phase: str
    order_sequence: int
    next_stage_id: int
    next_stage_name: str
    parent_id: int
    created_at: datetime
    updated_at: datetime