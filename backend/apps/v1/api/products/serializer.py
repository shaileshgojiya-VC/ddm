"""
Marshmallow serializers for Product data ingestion and response.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from marshmallow import INCLUDE, Schema, fields, post_dump, post_load
from sqlalchemy import Boolean, DateTime, Float, Integer

from apps.v1.api.products.models.model import Products
from core.utils.helper import TypeCoercion
from config.env_config import settings

logger = logging.getLogger(__name__)


class ProductSerializer(Schema):
    """Unified schema for both ingesting product data from JSON and serializing Product ORM objects to response format."""

    class Meta:
        unknown = INCLUDE
        render_as_key = True

    id = fields.Raw(data_key="id", attribute="id", allow_none=True)
    bitrix_id = fields.Raw(data_key="ID", attribute="bitrix_id", allow_none=True)
    NAME = fields.Raw(data_key="NAME", attribute="name", allow_none=True)
    CODE = fields.Raw(data_key="CODE", attribute="code", allow_none=True)
    ACTIVE = fields.Raw(data_key="ACTIVE", attribute="active", allow_none=True)
    CATEGORY = fields.Raw(
        data_key="Product Category", attribute="product_category", allow_none=True
    )
    CERTIFICATE = fields.Raw(
        data_key="Documents from factory – a.\tCOO       b. HC\t    c.\tFSC",
        attribute="documents_from_factory",
        allow_none=True,
    )
    PREVIEW_PICTURE = fields.Raw(
        data_key="PREVIEW_PICTURE", attribute="preview_picture", allow_none=True
    )
    DETAIL_PICTURE = fields.Raw(
        data_key="DETAIL_PICTURE", attribute="detail_picture", allow_none=True
    )
    SORT = fields.Raw(data_key="SORT", attribute="sort", allow_none=True)
    XML_ID = fields.Raw(data_key="XML_ID", attribute="xml_id", allow_none=True)
    TIMESTAMP_X = fields.Raw(data_key="TIMESTAMP_X", attribute="timestamp_x", allow_none=True)
    DATE_CREATE = fields.Raw(data_key="DATE_CREATE", attribute="date_create", allow_none=True)
    MODIFIED_BY = fields.Raw(data_key="MODIFIED_BY", attribute="modified_by", allow_none=True)
    CREATED_BY = fields.Raw(data_key="CREATED_BY", attribute="created_by", allow_none=True)
    CATALOG_ID = fields.Raw(data_key="CATALOG_ID", attribute="catalog_id", allow_none=True)
    SECTION_ID = fields.Raw(data_key="SECTION_ID", attribute="section_id", allow_none=True)
    DESCRIPTION = fields.Raw(data_key="DESCRIPTION", attribute="description", allow_none=True)
    DESCRIPTION_TYPE = fields.Raw(
        data_key="DESCRIPTION_TYPE", attribute="description_type", allow_none=True
    )
    PRICE = fields.Raw(data_key="PRICE", attribute="price", allow_none=True)
    CURRENCY_ID = fields.Raw(data_key="CURRENCY_ID", attribute="currency_id", allow_none=True)
    VAT_ID = fields.Raw(data_key="VAT_ID", attribute="vat_id", allow_none=True)
    VAT_INCLUDED = fields.Raw(data_key="VAT_INCLUDED", attribute="vat_included", allow_none=True)
    MEASURE = fields.Raw(data_key="MEASURE", attribute="measure", allow_none=True)
    Barcode = fields.Raw(data_key="Barcode", attribute="barcode", allow_none=True)
    Carton_Barcode = fields.Raw(
        data_key="Carton Barcode", attribute="carton_barcode", allow_none=True
    )
    Bestseller = fields.Raw(data_key="Bestseller", attribute="bestseller", allow_none=True)
    Special_Offer = fields.Raw(data_key="Special Offer", attribute="special_offer", allow_none=True)
    Product = fields.Raw(data_key="Product: ", attribute="product", allow_none=True)
    Art_number = fields.Raw(data_key="Art number", attribute="art_number", allow_none=True)
    Factory_Logo = fields.Raw(data_key="Factory Logo", attribute="factory_logo", allow_none=True)
    Specification = fields.Raw(
        data_key="Specification", attribute="specifications", allow_none=True
    )
    Product_Artwork = fields.Raw(
        data_key="Product Artwork", attribute="product_artwork", allow_none=True
    )
    Factory = fields.Raw(data_key="Factory", attribute="factory", allow_none=True)
    Country_of_Origin = fields.Raw(
        data_key="Country of Origin", attribute="country_of_origin", allow_none=True
    )
    HS_Code = fields.Raw(data_key="HS Code", attribute="hs_code", allow_none=True)
    Package_Material = fields.Raw(
        data_key="Package Material", attribute="package_material", allow_none=True
    )
    Net_Content = fields.Raw(data_key="Net Content", attribute="net_content", allow_none=True)
    Background_image = fields.Raw(
        data_key="Background image", attribute="background_image", allow_none=True
    )
    Shelf_Life = fields.Raw(data_key="Shelf Life", attribute="shelf_life", allow_none=True)
    Units_per_Carton = fields.Raw(
        data_key="Units per Carton (e.g., 12 x 1L)",
        attribute="units_per_carton",
        allow_none=True,
    )
    Loading_Quantities = fields.Raw(
        data_key="Loading Quantities", attribute="loading_quantities", allow_none=True
    )
    Product_Short_Name = fields.Raw(
        data_key="Product Short Name", attribute="product_short_name", allow_none=True
    )
    Link_to_Artwork_files = fields.Raw(
        data_key="Link to Artwork files",
        attribute="link_to_artwork_files",
        allow_none=True,
    )
    SKU_package = fields.Raw(
        data_key='SKU package (number of units per package, e.g., "10 slices", "4 cups")',
        attribute="sku_package",
        allow_none=True,
    )
    Cartons_per_Pallet = fields.Raw(
        data_key="Cartons per Pallet", attribute="cartons_per_pallet", allow_none=True
    )
    Carton_Artwork = fields.Raw(
        data_key="Carton Artwork", attribute="carton_artwork", allow_none=True
    )
    Photo_of_primary_packing = fields.Raw(
        data_key="Photo of primary packing",
        attribute="photo_of_primary_packing",
        allow_none=True,
    )
    Photo_of_secondary_packing = fields.Raw(
        data_key="Photo of secondary packing",
        attribute="photo_of_secondary_packing",
        allow_none=True,
    )
    Technical_data_sheet = fields.Raw(
        data_key="Technical data sheet",
        attribute="technical_data_sheet",
        allow_none=True,
    )
    Primary_packing_artwork = fields.Raw(
        data_key="Primary packing artwork",
        attribute="primary_packing_artwork",
        allow_none=True,
    )
    Secondary_packing_Artwork = fields.Raw(
        data_key="Secondary packing Artwork",
        attribute="secondary_packing_artwork",
        allow_none=True,
    )
    Transport_delivery_conditions_temperature = fields.Raw(
        data_key="Transport / delivery conditions - temperature ",
        attribute="transport_conditions_temperature",
        allow_none=True,
    )
    Storage_conditions_temperature = fields.Raw(
        data_key="Storage conditions – temperature",
        attribute="storage_conditions_temperature",
        allow_none=True,
    )
    Carton_dimensions = fields.Raw(
        data_key="Carton dimensions", attribute="carton_dimensions", allow_none=True
    )
    Pallet_dimensions = fields.Raw(
        data_key="Pallet dimensions", attribute="pallet_dimensions", allow_none=True
    )
    Lead_time_to_print_packing_material = fields.Raw(
        data_key="Lead time to print packing material",
        attribute="lead_time_to_print_packing_material",
        allow_none=True,
    )
    Lead_time_to_reorder_packing_material = fields.Raw(
        data_key="Lead time to reorder packing material",
        attribute="lead_time_to_reorder_packing_material",
        allow_none=True,
    )
    Lead_time_for_production = fields.Raw(
        data_key="Lead time for production",
        attribute="lead_time_to_production",
        allow_none=True,
    )
    Art_works_approved_by_FDA_of_country_of_destination = fields.Raw(
        data_key="Art works approved by FDA of country of destination ",
        attribute="art_works_approved_by_fda_of_country_of_destination",
        allow_none=True,
    )
    Loading_address = fields.Raw(
        data_key="Loading address ", attribute="loading_address", allow_none=True
    )
    Unit_pack_size = fields.Raw(
        data_key="Unit pack size ", attribute="unit_pack_size", allow_none=True
    )
    Packing = fields.Raw(data_key="Packing:", attribute="packing", allow_none=True)
    Carton = fields.Raw(data_key="Carton:", attribute="carton", allow_none=True)
    Term_of_delivery = fields.Raw(
        data_key="Term of delivery:", attribute="term_of_delivery", allow_none=True
    )
    Quantity = fields.Raw(data_key="Quantity:", attribute="quantity", allow_none=True)
    Origin = fields.Raw(data_key="Origin:", attribute="origin", allow_none=True)
    Product_Keylines = fields.Raw(
        data_key="Product Keylines", attribute="product_keylines", allow_none=True
    )
    MOQ_Packaging_Matereal = fields.Raw(
        data_key="MOQ - Packaging Matereal",
        attribute="moq_packaging_matereal",
        allow_none=True,
    )
    MOQ_Production = fields.Raw(
        data_key="MOQ - Production", attribute="moq_production", allow_none=True
    )

    @post_load
    def normalize_data(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Normalize and coerce types for database insertion."""
        # Build field to column mapping from schema fields
        field_to_column = {name: field.attribute or name for name, field in self.fields.items()}

        # Build column type mapping from SQLAlchemy model
        column_types = {}
        for col in Products.__table__.columns:
            if isinstance(col.type, Boolean):
                column_types[col.name] = TypeCoercion.coerce_bool
            elif isinstance(col.type, Integer):
                column_types[col.name] = TypeCoercion.coerce_int
            elif isinstance(col.type, Float):
                column_types[col.name] = TypeCoercion.coerce_float
            elif isinstance(col.type, DateTime):
                column_types[col.name] = TypeCoercion.coerce_datetime
            else:
                column_types[col.name] = TypeCoercion.coerce_str

        # Normalize data
        normalized = {}
        model_columns = {col.name for col in Products.__table__.columns}
        for key, value in data.items():
            column_name = field_to_column.get(key, key)
            if column_name in model_columns:
                coerce_func = column_types.get(column_name, TypeCoercion.coerce_str)
                normalized[column_name] = coerce_func(value) if value is not None else None

        return normalized

    @post_dump
    def format_output(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Format output values for response (e.g., booleans to Y/N, timestamps)."""
        bool_fields = [
            "ACTIVE",
            "VAT_INCLUDED",
            "Bestseller",
            "Special_Offer",
            "Art_works_approved_by_FDA_of_country_of_destination",
        ]
        timestamp_fields = ["TIMESTAMP_X", "DATE_CREATE"]

        # Ensure bitrix_id is in output (copy from ID if exists)
        if "ID" in data and "bitrix_id" not in data:
            data["bitrix_id"] = data["ID"]

        # Format boolean fields to Y/N
        for field in bool_fields:
            if field in data and data[field] is not None:
                if isinstance(data[field], bool):
                    data[field] = "Y" if data[field] else "N"
                elif isinstance(data[field], str) and data[field].upper() in ["Y", "N"]:
                    data[field] = data[field].upper()

        # Format timestamps
        for field in timestamp_fields:
            if field in data and data[field] and hasattr(data[field], "strftime"):
                data[field] = (
                    data[field].strftime("%Y-%m-%dT%H:%M:%S%z")
                    if data[field].tzinfo
                    else data[field].strftime("%Y-%m-%dT%H:%M:%S+03:00")
                )

        return data


class CategoryChildSerializer(Schema):
    """
    Category child serializer for nested child_categories array.
    Supports recursive nesting for hierarchical category structures.
    """

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    description = fields.Str(data_key="description", required=False, allow_none=True)
    status = fields.Str(data_key="status", required=True)
    product_count = fields.Int(
        data_key="product_count", required=False, allow_none=True, load_default=0
    )
    parent_id = fields.Str(data_key="parent_id", required=False, allow_none=True)
    sub_category_id = fields.Str(data_key="sub_category_id", required=False, allow_none=True)
    child_categories = fields.List(
        fields.Nested("CategoryChildSerializer"),
        data_key="child_categories",
        required=False,
        allow_none=True,
        load_default=[],
    )
    created_at = fields.DateTime(data_key="created_at", required=False, allow_none=True)
    updated_at = fields.DateTime(data_key="updated_at", required=False, allow_none=True)


class CategoryListSerializer(Schema):
    """
    Category serializer for GET /v1/product/category/list endpoint.
    Handles nested child categories recursively.
    """

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True)
    parent_id = fields.Str(data_key="parent_id", required=False, allow_none=True)
    sub_category_id = fields.Str(data_key="sub_category_id", required=False, allow_none=True)
    product_count = fields.Int(
        data_key="product_count", required=False, allow_none=True, load_default=0
    )
    child_categories = fields.List(
        fields.Nested(CategoryChildSerializer),
        data_key="child_categories",
        required=False,
        allow_none=True,
        load_default=[],
    )
    description = fields.Str(data_key="description", required=False, allow_none=True)
    status = fields.Str(data_key="status", required=True)
    created_at = fields.DateTime(data_key="created_at", required=True)
    updated_at = fields.DateTime(data_key="updated_at", required=True)


class CategorySerializer(Schema):
    """
    Category serializer for webhook operations (insert/update).
    Handles category data from Bitrix24 webhooks.
    """

    class Meta:
        unknown = INCLUDE
        render_as_key = True

    id = fields.Int(data_key="id", required=False, allow_none=True)
    bitrix_id = fields.Raw(data_key="bitrix_id", required=False, allow_none=True)
    parent_category_id = fields.Int(data_key="parent_category_id", required=False, allow_none=True)
    sub_category_id = fields.Int(data_key="sub_category_id", required=False, allow_none=True)
    catelog_id = fields.Int(data_key="catelog_id", required=False, allow_none=True)
    section_id = fields.Int(data_key="section_id", required=False, allow_none=True)
    name = fields.Str(data_key="name", required=False, allow_none=True)
    code = fields.Str(data_key="code", required=False, allow_none=True)


class CategoryListResponseSerializer(Schema):
    """
    Category list response serializer for GET /v1/product/category/list endpoint.
    Wraps the items array and all_product_count.
    """

    items = fields.List(
        fields.Nested(CategoryListSerializer),
        data_key="items",
        required=True,
    )
    all_product_count = fields.Int(
        data_key="all_product_count", required=False, allow_none=True, load_default=0
    )


class PaginationSerializer(Schema):
    """
    Pagination metadata serializer for paginated responses.
    Used in GET /v1/product/list/ endpoint.
    """

    page = fields.Int(data_key="page", required=True)
    limit = fields.Int(data_key="limit", required=True)
    total = fields.Int(data_key="total", required=True)
    pages = fields.Int(data_key="pages", required=True)


class ProductListItemSerializer(Schema):
    """
    Product list item serializer for nested product arrays.
    Used in supplier detail endpoints.
    """

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True, allow_none=True)
    description = fields.Str(
        data_key="description", required=False, allow_none=True, load_default=""
    )
    category = fields.Str(data_key="category", required=False, allow_none=True, load_default="")
    sub_category = fields.Str(
        data_key="sub_category", required=False, allow_none=True, load_default=""
    )
    parent_category = fields.Str(
        data_key="parent_category", required=False, allow_none=True, load_default=""
    )
    sku_package = fields.Str(
        data_key="sku_package", required=False, allow_none=True, load_default=""
    )

    image_url = fields.Str(data_key="image_url", required=False, allow_none=True, load_default="")
    price = fields.Float(data_key="price", required=False, allow_none=True)
    currency = fields.Str(data_key="currency", required=False, allow_none=True, load_default=None)
    primary_supplier_name = fields.Str(
        data_key="primary_supplier_name",
        required=False,
        allow_none=True,
        load_default="",
    )
    created_at = fields.Method("get_created_at", data_key="created_at", required=True)
    updated_at = fields.Method("get_updated_at", data_key="updated_at", required=True)
    status = fields.Str(data_key="status", required=True)

    def get_created_at(self, obj):
        """Get created_at as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("created_at")
        else:
            value = getattr(obj, "created_at", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None

    def get_updated_at(self, obj):
        """Get updated_at as ISO format string."""
        if isinstance(obj, dict):
            value = obj.get("updated_at")
        else:
            value = getattr(obj, "updated_at", None)

        if value:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                return value
        return None


class ProductListItemResponseSerializer(Schema):
    """
    Serializer for individual product items in list response.

    Used in GET /v1/product/list endpoint for each product item.
    Handles ProductListItem objects by extracting data from nested product and joined fields.
    """

    id = fields.Integer(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True, allow_none=True)
    sku_id = fields.Str(data_key="sku_id", required=True, allow_none=True)
    hs_code = fields.Str(data_key="hs_code", required=True, allow_none=True)
    units_per_carton = fields.Str(
        data_key="units_per_carton",
        required=False,
        allow_none=True,
        load_default="",
    )
    moq_packaging_matereal = fields.Str(
        data_key="moq_packaging_matereal",
        required=False,
        allow_none=True,
        load_default="",
    )
    moq_production = fields.Str(
        data_key="moq_production",
        required=False,
        allow_none=True,
        load_default="",
    )
    description = fields.Str(
        data_key="description",
        required=False,
        allow_none=True,
        load_default="",
    )
    category = fields.Str(
        data_key="category",
        required=False,
        allow_none=True,
        load_default="",
    )
    parent_category = fields.Str(
        data_key="parent_category",
        required=False,
        allow_none=True,
        load_default="",
    )
    sub_category = fields.Str(
        data_key="sub_category",
        required=False,
        allow_none=True,
        load_default="",
    )
    category_type = fields.Str(
        data_key="category_type",
        required=False,
        allow_none=True,
        load_default="",
    )
    image_url = fields.Str(
        data_key="image_url",
        required=False,
        allow_none=True,
        load_default="",
    )
    price = fields.Float(
        data_key="price",
        required=False,
        allow_none=True,
    )
    currency_id = fields.Str(
        data_key="currency_id",
        required=False,
        allow_none=True,
    )
    primary_supplier_name = fields.Str(
        data_key="primary_supplier_name",
        required=False,
        allow_none=True,
    )


class ProductListResponseSerializer(Schema):
    """
    Serializer for product list response data.

    Used in GET /v1/product/list endpoint to serialize the items array.
    """

    items = fields.List(
        fields.Nested(ProductListItemResponseSerializer),
        data_key="items",
        required=True,
    )


class PaginatedProductListResponseSerializer(Schema):
    """
    Paginated product list response serializer for GET /v1/product/list/ endpoint.
    Wraps status, pagination metadata, data items, and message.
    """

    status = fields.Str(data_key="status", required=True)
    pagination = fields.Nested(PaginationSerializer, data_key="pagination", required=True)
    data = fields.Nested(ProductListResponseSerializer, data_key="data", required=True)
    message = fields.Str(data_key="message", required=False, allow_none=True, load_default="")


class SupplierDetailSerializer(Schema):
    """
    Supplier detail serializer for nested supplier_details array.
    Modular serializer - can be modified independently for runtime response changes.
    Used in GET /v1/product/{id}/ endpoint.
    Maps Suppliers model fields to expected response format.
    """

    id = fields.Method("get_id", data_key="id", required=False, allow_none=True)
    supplier_name = fields.Method(
        "get_supplier_name", data_key="supplier_name", required=False, allow_none=True
    )
    bitrix_id = fields.Method(
        "get_bitrix_id", data_key="bitrix_id", required=False, allow_none=True
    )
    is_primary = fields.Method(
        "get_is_primary",
        data_key="is_primary",
        required=False,
        allow_none=True,
        load_default=False,
    )
    price = fields.Method("get_price", data_key="price", required=False, allow_none=True)
    currency = fields.Method("get_currency", data_key="currency", required=False, allow_none=True)
    country_of_origin = fields.Method(
        "get_country_of_origin",
        data_key="country_of_origin",
        required=False,
        allow_none=True,
    )
    moq = fields.Method("get_moq", data_key="moq", required=False, allow_none=True)
    lead_times = fields.Method(
        "get_lead_times", data_key="lead_times", required=False, allow_none=True
    )
    sku_id = fields.Method(
        "get_sku_id",
        data_key="sku_id",
        required=False,
        allow_none=True,
        load_default="",
    )
    rating = fields.Method("get_rating", data_key="rating", required=False, allow_none=True)
    status = fields.Method(
        "get_status",
        data_key="status",
        required=False,
        allow_none=True,
        load_default="active",
    )
    created_at = fields.Method(
        "get_created_at", data_key="created_at", required=False, allow_none=True
    )
    updated_at = fields.Method(
        "get_updated_at", data_key="updated_at", required=False, allow_none=True
    )

    def get_id(self, obj) -> Optional[str]:
        """Extract supplier ID."""
        if hasattr(obj, "id"):
            return str(obj.id)
        return None

    def get_supplier_name(self, obj) -> Optional[str]:
        """Extract supplier name from company_name attribute."""
        if hasattr(obj, "company_name"):
            return obj.company_name
        if hasattr(obj, "supplier_name"):
            return obj.supplier_name
        return None

    def get_bitrix_id(self, obj) -> Optional[str]:
        """Extract bitrix_id."""
        if hasattr(obj, "bitrix_id"):
            return str(obj.bitrix_id) if obj.bitrix_id is not None else None
        return None

    def get_is_primary(self, obj) -> bool:
        """Determine if supplier is primary (default to False)."""
        if hasattr(obj, "is_primary"):
            return obj.is_primary
        return False

    def get_price(self, obj) -> Optional[float]:
        """Extract price (not available on Suppliers model)."""
        if hasattr(obj, "price"):
            return obj.price
        return None

    def get_currency(self, obj) -> Optional[str]:
        """Extract currency from Suppliers model."""
        if hasattr(obj, "currency"):
            return obj.currency
        return None

    def get_country_of_origin(self, obj) -> Optional[str]:
        """Extract country_of_origin (not available on Suppliers model)."""
        if hasattr(obj, "country_of_origin"):
            return obj.country_of_origin
        return None

    def get_moq(self, obj) -> Optional[int]:
        """Extract MOQ (Minimum Order Quantity) from product or supplier object."""
        if hasattr(obj, "moq") and obj.moq is not None:
            return obj.moq
        if hasattr(obj, "moq_production") and obj.moq_production:
            return obj.moq_production
        if hasattr(obj, "moq_packaging_matereal") and obj.moq_packaging_matereal:
            return obj.moq_packaging_matereal
        return None

    def get_lead_times(self, obj) -> Optional[int]:
        """Extract lead times from product or supplier object."""
        if hasattr(obj, "lead_times") and obj.lead_times is not None:
            return obj.lead_times
        if hasattr(obj, "lead_time_to_production") and obj.lead_time_to_production:
            return obj.lead_time_to_production
        return None

    def get_sku_id(self, obj) -> str:
        """Extract sku_id (not available on Suppliers model)."""
        if hasattr(obj, "sku_id"):
            return obj.sku_id or ""
        return ""

    def get_rating(self, obj) -> Optional[float]:
        """Extract rating (not available on Suppliers model)."""
        if hasattr(obj, "rating"):
            return obj.rating
        return None

    def get_status(self, obj) -> str:
        """Extract status (default to active)."""
        if hasattr(obj, "deleted_at"):
            return "inactive" if obj.deleted_at is not None else "active"
        if hasattr(obj, "status"):
            return obj.status
        return "active"

    def get_created_at(self, obj) -> Optional[datetime]:
        """Extract created_at datetime."""
        if hasattr(obj, "created_at"):
            return obj.created_at
        return None

    def get_updated_at(self, obj) -> Optional[datetime]:
        """Extract updated_at datetime."""
        if hasattr(obj, "updated_at"):
            return obj.updated_at
        return None

    @post_dump
    def format_datetime(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Format datetime fields to ISO format string."""
        datetime_fields = ["created_at", "updated_at"]
        for field in datetime_fields:
            if field in data and data[field] and hasattr(data[field], "strftime"):
                data[field] = (
                    data[field].strftime("%Y-%m-%dT%H:%M:%S")
                    if not data[field].tzinfo
                    else data[field].strftime("%Y-%m-%dT%H:%M:%S%z")
                )
        return data


class CategoryItemSerializer(Schema):
    """
    Serializer for individual category items in list response.

    Used in GET /v1/product/category/list endpoint for each category item.
    Supports self-referential nested child_categories for 3-level hierarchy.

    Hierarchy Structure:
        Level 1 (Category): Dairy, Beverages, etc.
        Level 2 (Parent Category): UHT Milk, Yogurt, Butter, etc.
        Level 3 (Sub Category): UHT 1 Litre AT, UHT Bottle, etc.
    """

    id = fields.Str(data_key="id", required=True)
    name = fields.Str(data_key="name", required=True, allow_none=True)
    description = fields.Str(
        data_key="description",
        required=False,
        allow_none=True,
        load_default="",
    )
    status = fields.Str(
        data_key="status",
        required=False,
        allow_none=True,
        load_default="active",
    )
    product_count = fields.Int(
        data_key="product_count",
        required=False,
        allow_none=True,
        load_default=0,
    )
    parent_id = fields.Str(
        data_key="parent_id",
        required=False,
        allow_none=True,
    )
    subcategory_id = fields.Str(
        data_key="subcategory_id",
        required=False,
        allow_none=True,
    )
    # Self-referential nested field for hierarchical structure
    child_categories = fields.List(
        fields.Nested(lambda: CategoryItemSerializer()),
        data_key="child_categories",
        required=False,
        allow_none=True,
        load_default=[],
    )
    created_at = fields.DateTime(
        data_key="created_at",
        required=False,
        allow_none=True,
    )
    updated_at = fields.DateTime(
        data_key="updated_at",
        required=False,
        allow_none=True,
    )

    @post_dump
    def format_datetime(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Format datetime fields to ISO format string."""
        datetime_fields = ["created_at", "updated_at"]
        for field in datetime_fields:
            if field in data and data[field] and hasattr(data[field], "strftime"):
                data[field] = (
                    data[field].strftime("%Y-%m-%dT%H:%M:%S")
                    if not data[field].tzinfo
                    else data[field].strftime("%Y-%m-%dT%H:%M:%S%z")
                )
        return data


class CategoryListResponseSerializer(Schema):
    """
    Serializer for category list response data.

    Used in GET /v1/product/category/list endpoint to serialize the items array.
    """

    items = fields.List(
        fields.Nested(CategoryItemSerializer),
        data_key="items",
        required=True,
    )


class LogisticDetailSerializer(Schema):
    """
    Logistics detail serializer for nested logistics_details array.
    """

    id = fields.Str(data_key="id", required=False, allow_none=True)
    cartons_per_pallet = fields.Int(data_key="cartons_per_pallet", required=False, allow_none=True)
    loading_quantities = fields.List(
        fields.Str(), data_key="loading_quantities", required=False, allow_none=True
    )
    transport_temperature = fields.Str(
        data_key="transport_temperature",
        attribute="transport_delivery_conditions_temperature",
        required=False,
        allow_none=True,
    )
    storage_temperature = fields.Str(
        data_key="storage_temperature",
        attribute="storage_conditions_temperature",
        required=False,
        allow_none=True,
    )
    carton_dimensions = fields.Str(data_key="carton_dimensions", required=False, allow_none=True)
    pallet_dimensions = fields.Str(data_key="pallet_dimensions", required=False, allow_none=True)
    term_of_delivery = fields.Str(data_key="term_of_delivery", required=False, allow_none=True)


class DocumentDetailSerializer(Schema):
    """
    Document detail serializer for nested document_details array.
    Modular serializer - can be modified independently for runtime response changes.
    Used in GET /v1/product/{id}/ endpoint.
    """

    id = fields.Method("get_id", data_key="id", required=True)
    name = fields.Method("get_name", data_key="name", required=True)
    path = fields.Method("get_path", data_key="path", required=True)
    url = fields.Method("get_url", data_key="url", required=True, allow_none=True)
    file_name = fields.Method("get_file_name", data_key="file_name", required=True)
    file_type = fields.Method("get_file_type", data_key="file_type", required=True)
    file_size = fields.Method(
        "get_file_size", data_key="file_size", required=False, allow_none=True
    )
    status = fields.Method("get_status", data_key="status", required=True)
    created_at = fields.Method("get_created_at", data_key="created_at", required=True)
    updated_at = fields.Method("get_updated_at", data_key="updated_at", required=True)

    def get_id(self, obj) -> str:
        """Extract document ID as string."""
        if isinstance(obj, dict):
            return str(obj.get("id", "")) if obj.get("id") else ""
        if hasattr(obj, "id"):
            return str(obj.id)
        return ""

    def get_name(self, obj) -> str:
        """Extract document name from file_name (without extension)."""
        file_name = None
        if isinstance(obj, dict):
            file_name = obj.get("file_name")
        elif hasattr(obj, "file_name"):
            file_name = obj.file_name

        if file_name:
            # Remove file extension to get name
            name = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
            return name
        return ""

    def get_path(self, obj) -> str:
        """Extract and format document path."""
        # Otherwise, extract from document object

        doc_path = obj["path"] if isinstance(obj, dict) else obj.path
        
        return f"{settings.AZURE_BLOB_STORAGE_URL}/{(lambda p: json.loads(p).get('showUrl','') if p.lstrip().startswith('{') else p)(doc_path).lstrip('/')}" if doc_path else ""

    def get_url(self, obj) -> Dict[str, Any]:
        """Parse and format document URL, handling malformed JSON."""
        # If obj is a dict with pre-processed url, use it
        if isinstance(obj, dict):
            url_value = obj.get("url")
            if url_value is not None:
                return url_value if isinstance(url_value, dict) else {}

        # Otherwise, extract from document object
        doc_url = None
        if hasattr(obj, "url"):
            doc_url = obj.url

        if not doc_url:
            return {}

        # Parse URL safely - handle malformed JSON
        url_value = {}
        try:
            if isinstance(doc_url, dict):
                url_value = doc_url
            elif isinstance(doc_url, str):
                try:
                    url_value = json.loads(doc_url)
                    if not isinstance(url_value, dict):
                        url_value = {}
                except (json.JSONDecodeError, ValueError):
                    # If JSON parsing fails, try to extract partial data
                    try:
                        url_str = doc_url

                        # Try to extract showUrl and downloadUrl using regex
                        show_url_match = re.search(r'"showUrl"\s*:\s*"((?:[^"\\]|\\.)*)"', url_str)
                        download_url_match = re.search(
                            r'"downloadUrl"\s*:\s*"((?:[^"\\]|\\.)*)"?', url_str
                        )
                        # Also try to match incomplete downloadUrl (no closing quote)
                        if not download_url_match:
                            download_url_match = re.search(
                                r'"downloadUrl"\s*:\s*"((?:[^"\\]|\\.)*)', url_str
                            )

                        extracted_url = {}
                        if show_url_match:
                            extracted_url["showUrl"] = (
                                f"https://dana.bitrix24.eu{show_url_match.group(1)}"
                            )
                        if download_url_match:
                            extracted_url["downloadUrl"] = (
                                f"https://dana.bitrix24.eu{download_url_match.group(1)}"
                            )

                        if extracted_url:
                            url_value = extracted_url
                            logger.info(
                                f"Extracted partial URL data for document {getattr(obj, 'id', 'unknown')}"
                            )
                        else:
                            url_value = {}
                            logger.warning(
                                f"Could not extract URL data for document {getattr(obj, 'id', 'unknown')}: {doc_url[:100]}"
                            )
                    except Exception as extract_error:
                        logger.error(
                            f"Error extracting URL data for document {getattr(obj, 'id', 'unknown')}: {extract_error}",
                            exc_info=True,
                        )
                        url_value = {}
            else:
                url_value = {}
        except Exception as e:
            logger.error(
                f"Error processing URL for document {getattr(obj, 'id', 'unknown')}: {e}",
                exc_info=True,
            )
            url_value = {}

        return url_value

    def get_file_name(self, obj) -> str:
        """Extract file name."""
        if isinstance(obj, dict):
            return obj.get("file_name", "") or ""
        if hasattr(obj, "file_name"):
            return obj.file_name or ""
        return ""

    def get_file_type(self, obj) -> str:
        """Extract file type, removing 'application/' prefix if present."""
        file_type = None
        if isinstance(obj, dict):
            file_type = obj.get("file_type")
        elif hasattr(obj, "file_type"):
            file_type = obj.file_type

        if file_type:
            # Remove "application/" prefix if present
            if str(file_type).startswith("application/"):
                file_type = str(file_type).replace("application/", "")
            return str(file_type)

        # Try to extract from file_name extension
        file_name = None
        if isinstance(obj, dict):
            file_name = obj.get("file_name")
        elif hasattr(obj, "file_name"):
            file_name = obj.file_name

        if file_name and "." in file_name:
            return file_name.rsplit(".", 1)[1].lower()
        return ""

    def get_file_size(self, obj) -> Optional[int]:
        """Extract file size."""
        if isinstance(obj, dict):
            return obj.get("file_size")
        if hasattr(obj, "file_size"):
            return obj.file_size
        return None

    def get_status(self, obj) -> str:
        """Extract status (default to active)."""
        if isinstance(obj, dict):
            return obj.get("status", "active") or "active"
        if hasattr(obj, "status"):
            return obj.status
        if hasattr(obj, "deleted_at"):
            return "inactive" if obj.deleted_at is not None else "active"
        return "active"

    def get_created_at(self, obj) -> Optional[datetime]:
        """Extract created_at datetime."""
        if isinstance(obj, dict):
            return obj.get("created_at")
        if hasattr(obj, "created_at"):
            return obj.created_at
        return None

    def get_updated_at(self, obj) -> Optional[datetime]:
        """Extract updated_at datetime."""
        if isinstance(obj, dict):
            return obj.get("updated_at")
        if hasattr(obj, "updated_at"):
            return obj.updated_at
        return None

    @post_dump
    def format_datetime(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Format datetime fields to ISO format string and parse URL if needed."""
        datetime_fields = ["created_at", "updated_at"]
        for field in datetime_fields:
            if field in data and data[field] and hasattr(data[field], "strftime"):
                data[field] = (
                    data[field].strftime("%Y-%m-%dT%H:%M:%S")
                    if not data[field].tzinfo
                    else data[field].strftime("%Y-%m-%dT%H:%M:%S%z")
                )

        return data


class ProductResposeSerializer(Schema):
    """
    Serializer for product response data.
    Used in GET /v1/product/list endpoint to serialize the product response.
    """

    id = fields.Str(data_key="id", attribute="id", required=True, allow_none=True)
    name = fields.Str(data_key="name", attribute="name", required=True, allow_none=True)
    sku_id = fields.Str(data_key="sku_id", attribute="sku_id", required=True, allow_none=True)
    barcode = fields.Str(data_key="barcode", attribute="barcode", required=True, allow_none=True)
    hs_code = fields.Str(data_key="hs_code", attribute="hs_code", required=True, allow_none=True)
    carton_barcode = fields.Str(
        data_key="carton_barcode",
        attribute="carton_barcode",
        required=True,
        allow_none=True,
    )
    art_number = fields.Str(
        data_key="art_number", attribute="art_number", required=True, allow_none=True
    )
    unit_pack_size = fields.Int(
        data_key="unit_pack_size",
        attribute="unit_pack_size",
        required=True,
        allow_none=True,
    )
    units_per_cartoon = fields.Int(
        data_key="units_per_carton",
        attribute="units_per_carton",
        required=True,
        allow_none=True,
    )
    preview_text = fields.Method(
        "get_preview_text",
        data_key="preview_text",
        required=True,
        allow_none=True,
    )
    preview_picture = fields.Str(
        data_key="preview_picture",
        attribute="preview_picture",
        required=True,
        allow_none=True,
    )
    short_name = fields.Str(
        data_key="short_name",
        attribute="product_short_name",
        required=True,
        allow_none=True,
    )
    bitrix_url = fields.Method(
        "get_bitrix_url", data_key="bitrix_url", required=True, allow_none=True
    )
    bitrix_id = fields.Int(
        data_key="bitrix_id", attribute="bitrix_id", required=True, allow_none=True
    )
    description = fields.Str(
        data_key="description", attribute="description", required=True, allow_none=True
    )
    moq_production = fields.Int(
        data_key="moq_production", attribute="moq_production", required=True, allow_none=True
    )
    moq_packaging_matereal = fields.Int(
        data_key="moq_packaging_matereal",
        attribute="moq_packaging_matereal",
        required=True,
        allow_none=True,
    )
    lead_time_to_production = fields.Str(
        data_key="lead_time_to_production",
        attribute="lead_time_to_production",
        required=True,
        allow_none=True,
    )
    lead_time_to_print_packing_material = fields.Str(
        data_key="lead_time_to_print_packing_material",
        attribute="lead_time_to_print_packing_material",
        required=True,
        allow_none=True,
    )
    lead_time_to_reorder_packing_material = fields.Str(
        data_key="lead_time_to_reorder_packing_material",
        attribute="lead_time_to_reorder_packing_material",
        required=True,
        allow_none=True,
    )
    category = fields.Method("get_category", data_key="category", required=True, allow_none=True)
    sub_category = fields.Method(
        "get_sub_category", data_key="sub_category", required=True, allow_none=True
    )
    child_category = fields.Method(
        "get_child_category", data_key="child_category", required=True, allow_none=True
    )
    image_urls = fields.Method(
        "get_image_urls", data_key="image_urls", required=True, allow_none=True
    )
    price = fields.Float(data_key="price", attribute="price", required=True, allow_none=True)
    primary_supplier_name = fields.Str(
        data_key="primary_supplier_name",
        attribute="supplier_name",
        required=True,
        allow_none=True,
    )
    net_content = fields.Float(
        data_key="net_content", attribute="net_content", required=True, allow_none=True
    )
    net_content_unit = fields.Method(
        "get_net_content_unit",
        data_key="net_content_unit",
        required=True,
        allow_none=True,
    )
    shelf_life = fields.Int(
        data_key="shelf_life", attribute="shelf_life", required=True, allow_none=True
    )
    shelf_life_unit = fields.Method(
        "get_shelf_life_unit",
        data_key="shelf_life_unit",
        required=True,
        allow_none=True,
    )
    sku_package = fields.Str(
        data_key="sku_package", attribute="sku_package", required=True, allow_none=True
    )
    package_material = fields.Str(
        data_key="package_material",
        attribute="package_material",
        required=True,
        allow_none=True,
    )
    specification = fields.Str(
        data_key="specification",
        attribute="specifications",
        required=True,
        allow_none=True,
    )
    storage_conditions = fields.Str(
        data_key="storage_conditions",
        attribute="storage_conditions_temperature",
        required=True,
        allow_none=True,
    )
    brand_name = fields.Method(
        "get_brand_name", data_key="brand_name", required=True, allow_none=True
    )
    factory_name = fields.Str(
        data_key="factory_name", attribute="factory", required=True, allow_none=True
    )
    country_of_origin = fields.Str(
        data_key="country_of_origin",
        attribute="country_of_origin",
        required=True,
        allow_none=True,
    )
    origin = fields.Str(data_key="origin", attribute="origin", required=True, allow_none=True)
    loading_address = fields.Str(
        data_key="loading_address",
        attribute="loading_address",
        required=True,
        allow_none=True,
    )
    carton_dimensions = fields.Str(
        data_key="carton_dimensions",
        attribute="carton_dimensions",
        required=True,
        allow_none=True,
    )
    cartons_per_pallet = fields.Int(
        data_key="cartons_per_pallet",
        attribute="cartons_per_pallet",
        required=True,
        allow_none=True,
    )
    pallet_dimensions = fields.Str(
        data_key="pallet_dimensions",
        attribute="pallet_dimensions",
        required=True,
        allow_none=True,
    )
    active_from = fields.DateTime(
        data_key="active_from", attribute="active_from", required=True, allow_none=True
    )
    active_until = fields.DateTime(
        data_key="active_until",
        attribute="active_until",
        required=True,
        allow_none=True,
    )
    external_id = fields.Str(
        data_key="external_id", attribute="xml_id", required=True, allow_none=True
    )
    active_from = fields.DateTime(
        data_key="active_from", attribute="date_active_from", required=True, allow_none=True
    )
    active_to = fields.DateTime(
        data_key="active_to", attribute="date_active_to", required=True, allow_none=True
    )
    generated_by = fields.Method(
        "get_generated_by", data_key="generated_by", required=True, allow_none=True
    )
    created_by = fields.Str(
        data_key="created_by", attribute="created_by", required=True, allow_none=True
    )
    updated_by = fields.Method(
        "get_updated_by", data_key="updated_by", required=True, allow_none=True
    )
    created_at = fields.DateTime(
        data_key="created_at", attribute="created_at", required=True, allow_none=True
    )
    updated_at = fields.DateTime(
        data_key="updated_at", attribute="updated_at", required=True, allow_none=True
    )
    artwork_id = fields.Str(
        data_key="artwork_id",
        attribute="product_artwork",
        required=True,
        allow_none=True,
    )
    is_fda_approved = fields.Bool(
        data_key="is_fda_approved",
        attribute="art_works_approved_by_fda_of_country_of_destination",
        required=True,
        allow_none=True,
    )
    artwork_documents = fields.Method(
        "get_artwork_documents",
        data_key="artwork_documents",
        required=True,
        allow_none=False,
    )
    supplier_details = fields.Nested(
        SupplierDetailSerializer,
        data_key="supplier_details",
        many=True,
        required=True,
        allow_none=True,
    )
    logistics_details = fields.Nested(
        LogisticDetailSerializer,
        data_key="logistics_details",
        required=True,
        allow_none=True,
    )
    document_details = fields.Nested(
        DocumentDetailSerializer,
        data_key="document_details",
        many=True,
        required=True,
        allow_none=True,
    )

    def get_updated_by(self, obj):
        """Get updated_by from non-database attribute to avoid SQLAlchemy tracking."""
        return getattr(obj, "_serializer_updated_by", None)

    def get_generated_by(self, obj):
        """Get generated_by from non-database attribute to avoid SQLAlchemy tracking."""
        return getattr(obj, "_serializer_generated_by", None)

    def get_category(self, obj) -> Optional[str]:
        """Extract category name from parent_category_name (Level 1 - Root Category)."""
        if hasattr(obj, "parent_category_name"):
            return obj.parent_category_name or None
        return None

    def get_sub_category(self, obj) -> Optional[str]:
        """Extract sub category name from sub_category_name (Level 2 - Sub Category)."""
        if hasattr(obj, "sub_category_name"):
            return obj.sub_category_name or None
        return None

    def get_child_category(self, obj) -> Optional[str]:
        """Extract child category name from category_name (Level 3 - Child Category)."""
        if hasattr(obj, "category_name"):
            return obj.category_name or None
        return None

    def get_image_urls(self, obj) -> Optional[List[str]]:
        """Extract all image URLs from product."""
        image_urls = []
        if hasattr(obj, "preview_picture") and obj.preview_picture:
            image_urls.append(obj.preview_picture)
        if hasattr(obj, "detail_picture") and obj.detail_picture:
            image_urls.append(obj.detail_picture)
        if hasattr(obj, "background_image") and obj.background_image:
            image_urls.append(obj.background_image)
        return image_urls if image_urls else None

    def get_preview_text(self, obj) -> Optional[str]:
        """Extract preview text from description or preview_text attribute."""
        if hasattr(obj, "preview_text") and obj.preview_text:
            return obj.preview_text
        if hasattr(obj, "description") and obj.description:
            return obj.description
        return None

    def get_net_content_unit(self, obj) -> Optional[str]:
        """Extract net content unit (e.g., 'ml', 'g')."""
        if hasattr(obj, "net_content_unit") and obj.net_content_unit:
            return obj.net_content_unit
        return None

    def get_shelf_life_unit(self, obj) -> Optional[str]:
        """Extract shelf life unit (e.g., 'days', 'months')."""
        if hasattr(obj, "shelf_life_unit") and obj.shelf_life_unit:
            return obj.shelf_life_unit
        return None

    def get_brand_name(self, obj) -> Optional[str]:
        """Extract brand name."""
        if hasattr(obj, "brand_name") and obj.brand_name:
            return obj.brand_name
        return None

    def get_bitrix_url(self, obj) -> Optional[str]:
        """Construct Bitrix URL from bitrix_id."""
        if hasattr(obj, "bitrix_id") and obj.bitrix_id:
            return f"https://bitrix.com/product/{obj.bitrix_id}"
        return None

    def get_artwork_documents(self, obj) -> List[str]:
        """Extract artwork document URLs from document_details and product artwork fields."""
        artwork_docs = []
        if hasattr(obj, "document_details") and obj.document_details:
            for doc in obj.document_details:
                if hasattr(doc, "url") and doc.url:
                    artwork_docs.append(doc.url)
        if hasattr(obj, "product_artwork") and obj.product_artwork:
            artwork_docs.append(obj.product_artwork)
        if hasattr(obj, "link_to_artwork_files") and obj.link_to_artwork_files:
            artwork_docs.append(obj.link_to_artwork_files)
        if hasattr(obj, "carton_artwork") and obj.carton_artwork:
            artwork_docs.append(obj.carton_artwork)
        if hasattr(obj, "primary_packing_artwork") and obj.primary_packing_artwork:
            artwork_docs.append(obj.primary_packing_artwork)
        if hasattr(obj, "secondary_packing_artwork") and obj.secondary_packing_artwork:
            artwork_docs.append(obj.secondary_packing_artwork)
        return artwork_docs

    @post_dump
    def set_child_category(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Set child_category to same value as sub_category if child_category is None.
        This maintains backward compatibility.
        """
        if "child_category" not in data or data["child_category"] is None:
            if "sub_category" in data:
                data["child_category"] = data["sub_category"]
        return data


class ProductDetailResponseSerializer(Schema):
    """
    Product detail response wrapper serializer for GET /v1/product/{id}/ endpoint.
    Wraps product detail with status and message.
    Can be modified independently to change response structure.
    """

    status = fields.Str(data_key="status", required=True)
    data = fields.Nested(ProductResposeSerializer, data_key="data", required=True)
    message = fields.Str(data_key="message", required=False, allow_none=True, load_default="")
