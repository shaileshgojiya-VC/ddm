"""
List Request Service

Service for listing requests with filtering, sorting, and pagination.
"""

import logging
import math
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.request.models.model import Requests
from apps.v1.api.request.models.methods.method import RequestMethod
from apps.v1.api.request.serializer import RequestListItemSerializer
from apps.v1.api.products.models.model import Categories
from apps.v1.api.auth.models.model import Users
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse
from fastapi import status

logger = logging.getLogger(__name__)


class ListRequestService:
    """
    Service for listing requests with filters, sorting, and pagination.
    """

    def __init__(self):
        self.request_method = RequestMethod(Requests)

    def _get_valid_category_name(self, category: Categories) -> str:
        """
        Extract a valid category name from a Categories object.
        Filters out invalid values like "false", "null", empty strings, or JSON arrays.

        Args:
            category: Categories model instance

        Returns:
            Valid category name string or empty string if invalid
        """
        if not category:
            return ""

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

        return ""

    async def list_requests(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        priority: Optional[str] = None,
        phase: Optional[str] = None,
        request_status: Optional[str] = None,
        stage_id: Optional[int] = None,
        user_id: Optional[int] = None,
        country: Optional[str] = None,
        customer_id: Optional[int] = None,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
        current_user: Users = None,
    ):
        """
        List requests with filtering, sorting, and pagination.

        Args:
            db: Database session
            search: Search by uuid, customer_name, customer_email, bitrix_url, bitrix_id
            priority: Filter by priority (urgent, high, medium, low)
            phase: Filter by phase (lead, deal, registration)
            request_status: Filter by status (active, inactive)
            stage_id: Filter by stage id (1, 2, 3, etc.)
            user_id: Filter by user id (1, 2, 3, etc.)
            country: Filter by country
            customer_id: Filter by customer id (1, 2, 3, etc.)
            product_id: Filter by product id (1, 2, 3, etc.)
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
            sort_by: Sort by field (created_at, updated_at)
            sort_order: Sort order (asc, desc)
            page: Page number
            limit: Items per page

        Returns:
            StandardResponse with paginated request list
        """
        try:
            logger.info("Starting list_requests service")

            # Get requests, total count, and phase counts using method
            requests, total, data_counts = await self.request_method.list_requests(
                db=db,
                search=search,
                priority=priority,
                phase=phase,
                request_status=request_status,
                stage_id=stage_id,
                user_id=user_id,
                country=country,
                customer_id=customer_id,
                product_id=product_id,
                start_date=start_date,
                end_date=end_date,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                limit=limit,
                current_user=current_user,
            )

            # Get request IDs for optimized category fetching
            request_ids = [req.id for req in requests]

            # Fetch all categories in one optimized query using method
            categories_map = await self.request_method.get_categories_map(
                db=db, request_ids=request_ids
            )

            # Format request items
            formatted_items = []
            for request in requests:
                item = self._format_request_item(request, categories_map)
                formatted_items.append(item)

            # Serialize items
            serializer = RequestListItemSerializer()
            serialized_items = serializer.dump(formatted_items, many=True)

            # Calculate pages
            pages = math.ceil(total / limit) if limit > 0 else 0

            # Build response
            response_data = {
                "items": serialized_items,
                "data_count": data_counts,
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
                message=message_variable.REQUEST_LIST_SUCCESS,
            ).make

        except Exception as e:
            logger.error(f"Error in list_requests: {e}", exc_info=True)
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    def _format_request_item(
        self, request: Requests, categories_map: Dict[int, Categories] = None
    ) -> Dict[str, Any]:
        """
        Format a single request item for list response.

        Args:
            request: Request model instance

        Returns:
            Dictionary with formatted request data
        """
        # Get phase value
        phase_value = (
            str(request.phase.value)
            if hasattr(request.phase, "value")
            else str(request.phase) if request.phase else "lead"
        )

        # Get status value
        status_value = (
            str(request.request_status.value)
            if hasattr(request.request_status, "value")
            else str(request.request_status) if request.request_status else "active"
        )

        # Get customer details from request_customers relationship
        customer_name = None
        customer_email = None
        customer_country = None
        customer_full_name = None
        if request.request_customers:
            customer_mapping = request.request_customers[0]
            customer = customer_mapping.customer
            if customer:
                customer_name = customer.company_name if hasattr(customer, "company_name") else None
                customer_email = (
                    customer.email_ids[0]
                    if hasattr(customer, "email_ids")
                    and isinstance(customer.email_ids, list)
                    and customer.email_ids
                    else None
                )
                customer_country = customer.country if hasattr(customer, "country") else None
                customer_full_name = customer.full_name if hasattr(customer, "full_name") else None

        # Fallback to request fields if no customer found

        # Build request_id
        request_id = (
            request.deal_id
            or (
                " - ".join(
                    filter(
                        None,
                        [
                            request.lead,
                            customer_name,
                        ],
                    )
                )
            )
            or str(request.id)
        )

        # Build product category from products' categories table
        product_category_str = None
        if request.request_products:
            # Get first product's category
            first_product = (
                request.request_products[0].product if request.request_products else None
            )
            if first_product:
                # Get category hierarchy IDs in order: parent > sub > category
                category_ids_ordered = []
                if (
                    hasattr(first_product, "parent_category_id")
                    and first_product.parent_category_id
                ):
                    category_ids_ordered.append(first_product.parent_category_id)
                if hasattr(first_product, "sub_category_id") and first_product.sub_category_id:
                    category_ids_ordered.append(first_product.sub_category_id)
                if hasattr(first_product, "category_id") and first_product.category_id:
                    category_ids_ordered.append(first_product.category_id)

                # Build category path from categories_map
                # Format: "Main > sub > child_Category" as a single string
                if category_ids_ordered and categories_map:
                    category_path_parts = []
                    for cat_id in category_ids_ordered:
                        if cat_id in categories_map:
                            category = categories_map[cat_id]
                            category_name = self._get_valid_category_name(category)
                            # Only add valid category names (skip IDs and invalid values)
                            if category_name:
                                category_path_parts.append(category_name)

                    # Join valid category names with " > " separator
                    if category_path_parts:
                        product_category_str = " > ".join(category_path_parts)

        # Fallback to request.product_category if available (only if it's a list of valid strings)
        if (
            not product_category_str
            and request.product_category
            and isinstance(request.product_category, list)
        ):
            # Filter out invalid values (IDs, "false", null, etc.) from list
            valid_cats = []
            for cat in request.product_category:
                if not cat:
                    continue
                cat_str = str(cat).strip()
                # Skip if it's a number (likely an ID), "false", "null", or starts with "["
                if (
                    cat_str
                    and not cat_str.isdigit()  # Skip numeric IDs
                    and cat_str.lower() not in ("false", "null", "none", "")
                    and not cat_str.startswith("[")
                ):
                    valid_cats.append(cat_str)

            # Join valid category names with " > " separator
            if valid_cats:
                product_category_str = " > ".join(valid_cats)

        # Get stage name
        # First try from current_stage relationship
        stage_name = None
        if request.current_stage:
            stage_name = request.current_stage.stage_name

        # If not found, get from latest request_stage_activities
        if (
            not stage_name
            and hasattr(request, "request_stage_activities")
            and request.request_stage_activities
        ):
            # Sort activities by created_at (descending) and order_sequence (descending) to get the latest
            sorted_activities = sorted(
                request.request_stage_activities,
                key=lambda a: (
                    a.created_at if a.created_at else datetime.min,
                    a.order_sequence if a.order_sequence else 0,
                ),
                reverse=True,
            )

            # Get the latest activity's stage name
            for activity in sorted_activities:
                if hasattr(activity, "stage") and activity.stage:
                    if activity.stage.stage_name:
                        stage_name = activity.stage.stage_name
                        break

        # Get assigned_to user name
        assigned_to = None
        if request.assigned_to:
            assigned_to = request.assigned_to.name if hasattr(request.assigned_to, "name") else None

        # Build request item dictionary
        return {
            "id": str(request.id),  # Will be serialized as "uuid" in serializer
            "name": request.name or None,
            "phase": phase_value,
            "request_id": request_id,
            "customer_company_name": customer_name or None,
            "customer_email": customer_email or None,
            "customer_country": customer_country or None,
            "customer_full_name": customer_full_name or None,
            "priority": request.priority or None,
            "bitrix_url": request.bitrix_url or None,
            "bitrix_id": request.bitrix_id,
            "prodcut_category": product_category_str,
            "status": status_value,
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "stage_name": stage_name,
            "assigned_to": assigned_to,
        }
