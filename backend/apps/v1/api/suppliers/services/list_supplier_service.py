"""
List supplier service for retrieving supplier information with pagination and filters.
Refactored to use join queries and serializers.
"""

import logging
import math
from typing import Optional, Dict, Any
from datetime import date

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.suppliers.models.model import Suppliers
from apps.v1.api.suppliers.models.methods import SupplierMethod
from apps.v1.api.suppliers.serializer import SupplierListSerializer
from apps.v1.api.products.models.model import Categories
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ListSupplierService:
    """
    Service to list suppliers with filters, pagination, and sorting.
    Uses join queries and serializers for efficient data retrieval.
    """

    def __init__(self):
        self.supplier_method = SupplierMethod(Suppliers)
        self.supplier_serializer = SupplierListSerializer()

    async def list_suppliers(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        country: Optional[str] = None,
        company_type: Optional[str] = None,
        category_id: Optional[int] = None,
        sub_category_id: Optional[int] = None,
        child_category_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ):
        """
        List suppliers with optional filters, sorting, and pagination.

        Args:
            db: Database session
            search: Search by uuid, name, or email
            country: Filter by country
            company_type: Filter by company type
            category_id: Filter by category id (1, 2, 3, etc.)
            sub_category_id: Filter by sub_category id (1, 2, 3, etc.)
            child_category_id: Filter by child_category id (1, 2, 3, etc.)
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            sort_by: Field to sort by (created_at, updated_at)
            sort_order: Sort order (asc, desc)
            page: Page number
            limit: Items per page

        Returns:
            StandardResponse with paginated supplier list
        """
        try:
            logger.info("Starting list_suppliers service")

            # Get suppliers and total count using method
            suppliers, total = await self.supplier_method.list_suppliers(
                db=db,
                search=search,
                country=country,
                company_type=company_type,
                category_id=category_id,
                sub_category_id=sub_category_id,
                child_category_id=child_category_id,
                start_date=start_date,
                end_date=end_date,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                limit=limit,
            )

            # Collect all category IDs from products
            all_category_ids = set()
            for supplier in suppliers:
                # Access product_suppliers relationship
                product_suppliers = getattr(supplier, "product_suppliers", [])
                if product_suppliers:
                    for ps_mapping in product_suppliers:
                        product = getattr(ps_mapping, "product", None) if ps_mapping else None
                        if product:
                            if (
                                hasattr(product, "parent_category_id")
                                and product.parent_category_id
                            ):
                                all_category_ids.add(product.parent_category_id)
                            if hasattr(product, "sub_category_id") and product.sub_category_id:
                                all_category_ids.add(product.sub_category_id)
                            if hasattr(product, "category_id") and product.category_id:
                                all_category_ids.add(product.category_id)

            # Fetch all categories in one query using method
            categories_map = await self.supplier_method.get_categories_map(
                db=db, category_ids=list(all_category_ids)
            )

            # Format supplier items
            formatted_items = []
            for supplier in suppliers:
                item = self._format_supplier_item(supplier, categories_map)
                formatted_items.append(item)

            # Serialize items
            serialized_items = self.supplier_serializer.dump(formatted_items, many=True)

            # Calculate pages
            pages = math.ceil(total / limit) if limit > 0 else 0

            # Build response
            response_data = {
                "items": serialized_items,
            }
            pagination_data = {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": pages,
            }

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=response_data,
                pagination=pagination_data,
                message=message_variable.SUPPLIERS_RETRIEVED_SUCCESS,
            ).make

        except Exception as e:
            logger.error(f"Error in list_suppliers: {e}", exc_info=True)
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    def _get_valid_category_name(self, category: Categories) -> Optional[str]:
        """
        Extract a valid category name from a Categories object.
        Filters out invalid values like "false", "null", empty strings, or JSON arrays.

        Args:
            category: Categories model instance

        Returns:
            Valid category name string or None
        """
        if not category:
            return None

        # Try name first
        if hasattr(category, "name") and category.name:
            name_val = str(category.name).strip()
            # Filter out invalid values
            if (
                name_val
                and name_val.lower() not in ("false", "null", "none", "")
                and not name_val.startswith("[")
            ):
                return name_val

        # Fallback to code
        if hasattr(category, "code") and category.code:
            code_val = str(category.code).strip()
            # Filter out invalid values
            if (
                code_val
                and code_val.lower() not in ("false", "null", "none", "")
                and not code_val.startswith("[")
            ):
                return code_val

        return None

    def _format_supplier_item(
        self, supplier: Suppliers, categories_map: Dict[int, Categories] = None
    ) -> Dict[str, Any]:
        """
        Format a single supplier item for list response.

        Args:
            supplier: Supplier model instance
            categories_map: Dictionary mapping category IDs to Categories objects

        Returns:
            Dictionary with formatted supplier data
        """
        # Build category arrays from all products
        category_list = []
        sub_category_list = []
        child_category_list = []

        # Access product_suppliers relationship
        product_suppliers = getattr(supplier, "product_suppliers", [])
        if product_suppliers:
            for ps_mapping in product_suppliers:
                product = getattr(ps_mapping, "product", None) if ps_mapping else None
                if product:
                    # Collect category IDs
                    if hasattr(product, "parent_category_id") and product.parent_category_id:
                        category_list.append(product.parent_category_id)
                    if hasattr(product, "sub_category_id") and product.sub_category_id:
                        sub_category_list.append(product.sub_category_id)
                    if hasattr(product, "category_id") and product.category_id:
                        child_category_list.append(product.category_id)

        # Build category name arrays from categories_map
        category_names = []
        for cat_id in set(category_list):
            if cat_id in categories_map:
                cat_name = self._get_valid_category_name(categories_map[cat_id])
                if cat_name and cat_name not in category_names:
                    category_names.append(cat_name)

        sub_category_names = []
        for cat_id in set(sub_category_list):
            if cat_id in categories_map:
                cat_name = self._get_valid_category_name(categories_map[cat_id])
                if cat_name and cat_name not in sub_category_names:
                    sub_category_names.append(cat_name)

        child_category_names = []
        for cat_id in set(child_category_list):
            if cat_id in categories_map:
                cat_name = self._get_valid_category_name(categories_map[cat_id])
                if cat_name and cat_name not in child_category_names:
                    child_category_names.append(cat_name)

        # Fallback to supplier.product_category if no categories found
        if not category_names and supplier.product_category:
            if isinstance(supplier.product_category, str):
                # Filter out invalid values
                cat_val = str(supplier.product_category).strip()
                if (
                    cat_val
                    and cat_val.lower() not in ("false", "null", "none", "")
                    and not cat_val.startswith("[")
                ):
                    category_names = [cat_val]
            elif isinstance(supplier.product_category, list):
                # Filter out invalid values from list
                category_names = [
                    str(cat).strip()
                    for cat in supplier.product_category
                    if cat
                    and str(cat).strip()
                    and str(cat).strip().lower() not in ("false", "null", "none", "")
                    and not str(cat).strip().startswith("[")
                ]

        # Format email (handle JSON array)
        email_str = None
        if supplier.email:
            if isinstance(supplier.email, list) and len(supplier.email) > 0:
                email_value = (
                    supplier.email[0].get("VALUE")
                    if isinstance(supplier.email[0], dict)
                    else supplier.email[0]
                )
                email_str = email_value or None
            elif isinstance(supplier.email, str):
                email_str = supplier.email

        # Format phone (handle JSON array)
        phone_str = None
        if supplier.phone:
            if isinstance(supplier.phone, list) and len(supplier.phone) > 0:
                phone_value = (
                    supplier.phone[0].get("VALUE")
                    if isinstance(supplier.phone[0], dict)
                    else supplier.phone[0]
                )
                phone_str = phone_value or None
            elif isinstance(supplier.phone, str):
                phone_str = supplier.phone

        # Build address
        address_parts = [
            supplier.street_address or "",
            supplier.city or "",
            supplier.zip or "",
            supplier.state or "",
        ]
        address = ", ".join(filter(None, address_parts)).strip()

        # Build supplier item dictionary
        return {
            "id": str(supplier.id),
            "company_name": supplier.company_name or "",
            "email": email_str,
            "phone_number": phone_str,
            "rating": float(supplier.stars) if supplier.stars is not None else 0.0,
            "address": address,
            "country": supplier.country or "",
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at,
            "last_contact": supplier.last_contact or None,
            "prefix": supplier.prefix or None,
            "company_type": supplier.company_type or None,
            "category": category_names,
            "sub_category": sub_category_names,
            "child_category": child_category_names,
        }
