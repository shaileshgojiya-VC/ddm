"""
List product service for retrieving paginated product information with filters.
"""

import logging
import math
from typing import Optional
from datetime import date

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.products.models.methods import ProductListDatabaseHelper
from apps.v1.api.products.serializer import ProductListResponseSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ListProductService:
    """
    Service class for listing products with filters, pagination, and sorting.

    Provides business logic for retrieving paginated product lists
    with support for search, category filtering, and sorting options.
    """

    async def list_products(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        sub_category_id: Optional[str] = None,
        child_category_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 10,
    ):
        """
        List products with optional filters, sorting, and pagination.

        Args:
            db: Database session
            search: Search term for id or name
            category_id: Filter by category id
            sub_category_id: Filter by sub category id
            child_category_id: Filter by child category id
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            sort_by: Field to sort by (created_at, updated_at)
            sort_order: Sort order (asc, desc)
            page: Page number (default 1)
            limit: Items per page (default 10)

        Returns:
            StandardResponse with paginated product list
        """
        try:
            logger.info("STEP 1: Starting product list retrieval workflow")

            logger.info("STEP 2: Validating pagination parameters")
            page = max(1, page)
            limit = min(max(1, limit), 100)

            logger.info(
                f"STEP 3: Fetching products with filters - search: {search}, "
                f"category_id: {category_id}, sub_category_id: {sub_category_id}, "
                f"child_category_id: {child_category_id}, start_date: {start_date}, "
                f"end_date: {end_date}, sort_by: {sort_by}, "
                f"sort_order: {sort_order}, page: {page}, limit: {limit}"
            )

            items, total = await ProductListDatabaseHelper.fetch_product_list(
                db=db,
                page=page,
                limit=limit,
                search=search,
                category_id=category_id,
                sub_category_id=sub_category_id,
                child_category_id=child_category_id,
                start_date=start_date,
                end_date=end_date,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            logger.info(f"STEP 4: Found {len(items)} products, total: {total}")

            logger.info("STEP 5: Calculating pagination metadata")
            total_pages = math.ceil(total / limit) if limit > 0 else 0

            pagination_data = {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": total_pages,
            }

            logger.info("STEP 6: Transforming product items to dictionary format")
            # Transform Products objects to dictionaries with direct field mappings
            formatted_items = []
            for product in items:
                formatted_item = {
                    "id": product.id,
                    "name": product.name or None,
                    "sku_id": product.sku_id or None,
                    "hs_code": product.hs_code or None,
                    "units_per_carton": (
                        str(product.units_per_carton) if product.units_per_carton else ""
                    ),
                    "moq_packaging_matereal": (
                        str(product.moq_packaging_matereal)
                        if product.moq_packaging_matereal
                        else ""
                    ),
                    "moq_production": str(product.moq_production) if product.moq_production else "",
                    "description": product.description or "",
                    "category": getattr(product, "category_name", None) or "",
                    "parent_category": getattr(product, "parent_category_name", None) or "",
                    "sub_category": getattr(product, "sub_category_name", None) or "",
                    "category_type": product.category_type or "",
                    "image_url": getattr(product, "image_url", None) or "",
                    "price": product.price if product.price is not None else None,
                    "currency_id": str(product.currency_id) if product.currency_id else None,
                    "primary_supplier_name": getattr(product, "primary_supplier_name", None)
                    or None,
                }
                formatted_items.append(formatted_item)

            logger.info("STEP 7: Serializing response data")
            response_data = {
                "items": formatted_items,
            }

            serializer = ProductListResponseSerializer()
            serialized_data = serializer.dump(response_data)

            logger.info("STEP 8: Building final response")

            logger.info("STEP 9: Product list retrieval completed successfully")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_data,
                pagination=pagination_data,
                message=message_variable.PRODUCTS_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"STEP ERROR: Validation error in list_products: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=str(exc),
            ).make

        except Exception as exc:
            logger.error(
                f"STEP ERROR: Unexpected error in list_products: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
