"""
List category service for retrieving category information with hierarchy.

Provides business logic for retrieving category lists with child categories
and product counts.
"""

import logging
from typing import Optional

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.products.models.methods import CategoryListDatabaseHelper
from apps.v1.api.products.serializer import CategoryListResponseSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ListCategoryService:
    """
    Service class for listing categories with hierarchy and product counts.

    Provides business logic for retrieving category lists with child categories,
    product counts, and sorting options.
    """

    async def list_categories(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 10,
    ):
        """
        List categories with child categories and product counts.

        Args:
            db: Database session
            search: Search term for category name (case-insensitive)
            sort_by: Field to sort by (created_at, updated_at)
            sort_order: Sort order (asc, desc)

        Returns:
            StandardResponse with category list and total product count
        """
        try:
            logger.info("STEP 1: Starting category list retrieval workflow")
            page = max(1, page)
            limit = min(max(1, limit), 100)

            logger.info(
                f"STEP 2: Fetching categories with filters - search: {search}, "
                f"sort_by: {sort_by}, sort_order: {sort_order}"
            )

            items, total_product_count = await CategoryListDatabaseHelper.fetch_category_list(
                db=db,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            logger.info(f"STEP 3: Found {len(items)} categories")

            logger.info("STEP 4: Serializing response data")
            response_data = {
                "items": items,
            }

            serializer = CategoryListResponseSerializer()
            serialized_data = serializer.dump(response_data)

            logger.info("STEP 5: Building final response")
            serialized_data["total_product_count"] = total_product_count

            logger.info("STEP 6: Category list retrieval completed successfully")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_data,
                message=message_variable.CATEGORIES_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"STEP ERROR: Validation error in list_categories: {exc}",
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
                f"STEP ERROR: Unexpected error in list_categories: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
