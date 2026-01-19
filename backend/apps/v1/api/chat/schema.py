"""
Chat API Pydantic schemas.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CreateGroupRequest(BaseModel):
    """Schema for creating a new message group."""
    
    group_name: str = Field(..., description="Name of the group", min_length=1, max_length=255)
    members: List[int] = Field(..., description="List of user IDs to add as members", min_items=1)


class UpdateGroupRequest(BaseModel):
    """Schema for updating an existing message group."""

    group_name: Optional[str] = Field(None, description="Updated group name", min_length=1, max_length=255)
    members: Optional[List[int]] = Field(None, description="Updated list of user IDs", min_items=1)


class GroupResponse(BaseModel):
    """Schema for group response."""
    
    id: int
    uuid: str
    group_name: Optional[str]
    created_by: Optional[int]
    members: Optional[List[int]]
    admins: Optional[List[int]]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True

