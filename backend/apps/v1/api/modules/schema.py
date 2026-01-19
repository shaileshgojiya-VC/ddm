"""
Module API Pydantic schemas.
"""

from pydantic import BaseModel
from typing import Optional


class ListModulesQueryParams(BaseModel):
    """Query parameters for listing modules."""

    page: int = 1
    limit: int = 10
    search: Optional[str] = None

