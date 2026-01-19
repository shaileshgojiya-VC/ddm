"""
Service for retrieving dashboard filters.

This service handles the business logic for fetching and populating
filter options for the dashboard-management module.

Filter Type Responsibilities:
- date_range: Returns min_date and max_date only (date picker)

All filters include normalization and deduplication for clean UI consumption.
"""

import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.api_filters.models.method import DashboardFilterDatabaseMethods
from apps.v1.api.api_filters.registry import (
    FILTER_REGISTRY,
    FILTER_TYPES,
)
from apps.v1.api.api_filters.serilizer import InquiryFilterResponseSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class DashboardFilterService:
    """
    Service class for retrieving dashboard filters.

    Provides business logic for fetching filter configurations
    and populating options from database.
    """

    async def get_dashboard_filters(
        self,
        db: AsyncSession,
        module: str,
    ):
        """
        Retrieve filters for dashboard-management module with populated options.

        Args:
            db: Database session
            module: Module name (should be 'dashboard-management')

        Returns:
            StandardResponse with filter configuration and options
        """
        try:
            logger.info("STEP 1: Starting dashboard filter retrieval workflow")

            logger.info(f"STEP 2: Validating module: {module}")

            if module not in FILTER_REGISTRY:
                logger.error(f"Invalid module requested: {module}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.INVALID_MODULE,
                ).make

            logger.info("STEP 3: Fetching filter configuration from registry")
            filter_config = FILTER_REGISTRY[module]

            logger.info("STEP 4: Initializing database methods")
            db_methods = DashboardFilterDatabaseMethods(db)

            logger.info("STEP 5: Building filters with type-specific fields")
            filters = {}

            for filter_name, filter_def in filter_config.items():
                filter_type = filter_def.get("type")
                filter_label = filter_def.get("label", f"All {filter_name.title()}")

                filters[filter_name] = {
                    "key": filter_name,
                    "label": filter_label,
                    "type": filter_type,
                }

                logger.info(
                    f"STEP 5.{filter_name}: Processing {filter_name} filter (type: {filter_type})"
                )

                if filter_type == FILTER_TYPES["DATE_RANGE"]:
                    logger.info(f"STEP 5.{filter_name}: Fetching date range metadata")
                    date_range_data = await db_methods.get_date_range()
                    filters[filter_name]["min_date"] = date_range_data.get("min_date")
                    filters[filter_name]["max_date"] = date_range_data.get("max_date")
                    logger.info(
                        f"STEP 5.{filter_name}: Date range configured: {date_range_data}"
                    )

                else:
                    logger.warning(
                        f"STEP 5.{filter_name}: Unknown filter type: {filter_type}"
                    )

            logger.info("STEP 6: Building final response data")
            response_data = {
                "module": module,
                "filters": filters,
            }

            logger.info("STEP 7: Serializing response data")
            filter_serializer = InquiryFilterResponseSerializer()
            serialized_data = filter_serializer.dump(response_data)

            logger.info("STEP 8: Building final response")

            logger.info("STEP 9: Dashboard filters retrieved successfully")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_data,
                message=message_variable.FILTERS_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"STEP ERROR: Validation error in get_dashboard_filters: {exc}",
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
                f"STEP ERROR: Unexpected error in get_dashboard_filters: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
