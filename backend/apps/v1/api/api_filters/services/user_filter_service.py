"""
Service for retrieving user management filters.

This service handles the business logic for fetching and populating
filter options for the users-management module.

Filter Type Responsibilities:
- static: Returns options array (dropdown filters)
- search: Returns placeholder only (text input)

All filters include normalization and deduplication for clean UI consumption.
"""

import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.api_filters.models.method import UserFilterDatabaseMethods
from apps.v1.api.api_filters.registry import (
    FILTER_REGISTRY,
    FILTER_TYPES,
    STATIC_OPTIONS,
)
from apps.v1.api.api_filters.serilizer import InquiryFilterResponseSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class UserFilterService:
    """
    Service class for retrieving user management filters.

    Provides business logic for fetching filter configurations
    and populating options from static sources.
    """

    async def get_user_filters(
        self,
        db: AsyncSession,
        module: str,
    ):
        """
        Retrieve filters for users-management module with populated options.

        Args:
            db: Database session
            module: Module name (should be 'users-management')

        Returns:
            StandardResponse with filter configuration and options
        """
        try:
            logger.info("STEP 1: Starting user filter retrieval workflow")

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

                if filter_type == FILTER_TYPES["STATIC"]:
                    options_key = filter_def.get("options_key")
                    if options_key and options_key in STATIC_OPTIONS:
                        static_options = STATIC_OPTIONS[options_key]
                        filters[filter_name]["options"] = self._add_default_option(
                            static_options, filter_label
                        )
                        logger.info(
                            f"STEP 5.{filter_name}: Loaded static options for {options_key}"
                        )
                    else:
                        filters[filter_name]["options"] = self._add_default_option(
                            [], filter_label
                        )
                        logger.warning(
                            f"STEP 5.{filter_name}: No static options found for {options_key}"
                        )

                elif filter_type == FILTER_TYPES["SEARCH"]:
                    placeholder = filter_def.get("placeholder", "")
                    filters[filter_name]["placeholder"] = placeholder
                    logger.info(
                        f"STEP 5.{filter_name}: Configured search filter with placeholder"
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

            logger.info("STEP 9: User filters retrieved successfully")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_data,
                message=message_variable.FILTERS_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"STEP ERROR: Validation error in get_user_filters: {exc}",
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
                f"STEP ERROR: Unexpected error in get_user_filters: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    def _add_default_option(self, options: list, label: str) -> list:
        """
        Add default "All X" option at the beginning of options list.
        Replaces existing "All" or "All X" option if present.

        Args:
            options: List of option dictionaries
            label: Default label (e.g., "All Countries", "All Types")

        Returns:
            List with default option prepended
        """
        default_option = {"label": label, "value": ""}

        if not options:
            return [default_option]

        # Remove any existing default option (empty value, "all" value, or "All" label)
        filtered_options = [
            opt
            for opt in options
            if opt.get("value") not in ("", "all", None)
            and not (
                isinstance(opt.get("label"), str)
                and opt.get("label", "").lower().startswith("all")
            )
        ]

        return [default_option] + filtered_options
