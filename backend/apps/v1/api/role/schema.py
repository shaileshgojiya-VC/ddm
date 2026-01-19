"""
Role API Pydantic schemas.
"""

from pydantic import BaseModel
from typing import Optional


class ListRolesQueryParams(BaseModel):
    """Query parameters for listing roles."""

    page: int = 1
    limit: int = 10
    search: Optional[str] = None

