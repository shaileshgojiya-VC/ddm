from typing import Generic, Optional, TypeVar

from fastapi import Query
from fastapi_pagination.default import Page as BasePage
from fastapi_pagination.default import Params as BaseParams

T = TypeVar("T")


class Params(BaseParams):
    page: int = Query(1,ge=0, description="Page number")
    size: Optional[int] = Query(None,ge=0, le=100, description="Page size")


class Page(BasePage[T], Generic[T]):
    __params_type__ = Params        