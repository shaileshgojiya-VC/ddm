from enum import Enum


class DocumentSource(Enum):
    EMAIL = "email"
    BITRIX = "bitrix"
    ONEDRIVE = "onedrive"


class SourceTable(Enum):
    SUPPLIERS = "suppliers"
    PRODUCTS = "products"
    REQUESTS = "requests"