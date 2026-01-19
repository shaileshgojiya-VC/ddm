"""
Bitrix webhook Pydantic schemas.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class BitrixWebhookRequest(BaseModel):
    """
    Schema for Bitrix webhook request.
    Bitrix24 can send data in various formats, so we make fields flexible.
    """

    event: str
    data: Union[Dict[str, Any], list, str] = Field(default_factory=dict)
    ts: Optional[str] = None
    auth: Optional[Union[Dict[str, Any], str]] = None
    event_handler_id: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow extra fields that Bitrix might send


class WebhookDataRequest(BaseModel):
    """
    Schema for webhook data management API.
    Handles insert, update, and delete operations for all tables.
    """

    eventtype: str = Field(..., description="Operation type: insert, update, or delete")
    table: str = Field(..., description="Table name (product, supplier, customer, request, etc.)")
    data: Dict[str, Any] = Field(..., description="Table-related data (will be validated with serializer)")
    bitrix_id: Optional[str] = Field(None, description="Bitrix ID for the record")
    mapping: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, 
        description="Mapping data for bridge tables (always in list format)"
    )
    webhook: str = Field(..., description="Webhook source: bitrix or outlook")
    
    class Config:
        extra = "allow"  # Allow extra fields
