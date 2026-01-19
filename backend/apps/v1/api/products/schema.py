"""
Pydantic schemas for Product API requests and responses.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class ProductFull(BaseModel):
    """Full product schema with all fields."""

    class Config:
        from_attributes = True
        extra = "allow"

    # Allow any fields from the JSON response
    def __init__(self, **data: Any):
        super().__init__(**data)


class CategoryChildSchema(BaseModel):
    """Category child schema for nested child_categories array."""

    uuid: str
    name: str
    description: Optional[str] = None
    status: str
    product_count: int = 0
    parent_uuid: Optional[str] = None
    subcategory_uuid: Optional[str] = None
    child_categories: List["CategoryChildSchema"] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class CategoryItemSchema(BaseModel):
    """Category item schema for items array."""

    uuid: str
    name: str
    parent_uuid: Optional[str] = None
    subcategory_uuid: Optional[str] = None
    product_count: int = 0
    child_categories: List[CategoryChildSchema] = []
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryListResponseSchema(BaseModel):
    """Category list response schema for GET /v1/product/category/list endpoint."""

    items: List[CategoryItemSchema]
    all_product_count: int = 0

    class Config:
        from_attributes = True


class ListProductsQueryParams(BaseModel):
    """Query parameters for listing products."""

    search: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    child_category: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    page: int = 1
    limit: int = 10

    class Config:
        from_attributes = True
