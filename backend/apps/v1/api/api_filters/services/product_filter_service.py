"""
Service for retrieving product management filters.

This service handles the business logic for fetching and populating
filter options for the product-management module.

Filter Type Responsibilities:
- static/dynamic: Returns options array (dropdown filters)
- search: Returns placeholder only (text input)

All filters include normalization and deduplication for clean UI consumption.
"""

import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.api_filters.models.method import ProductFilterDatabaseMethods
from apps.v1.api.api_filters.registry import (
    FILTER_REGISTRY,
    FILTER_TYPES,
    STATIC_OPTIONS,
)
from apps.v1.api.api_filters.serilizer import InquiryFilterResponseSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ProductFilterService:
    """
    Service class for retrieving product management filters.

    Provides business logic for fetching filter configurations
    and populating options from static sources and database.

    Key Features:
    - Type-specific field inclusion (only relevant fields per filter type)
    - Normalization of Bitrix raw values
    - Deduplication by value
    - Clean, UI-friendly response structure
    """

    async def get_product_filters(
        self,
        db: AsyncSession,
        module: str,
    ):
        """
        Retrieve filters for product-management module with populated options.

        Args:
            db: Database session
            module: Module name (should be 'product-management')

        Returns:
            StandardResponse with filter configuration and options
        """
        try:
            logger.info("STEP 1: Starting product filter retrieval workflow")

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
            db_methods = ProductFilterDatabaseMethods(db)

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
                        filters[filter_name]["options"] = self._add_default_option([], filter_label)
                        logger.warning(
                            f"STEP 5.{filter_name}: No static options found for {options_key}"
                        )

                elif filter_type == FILTER_TYPES["DYNAMIC"]:
                    source = filter_def.get("source")
                    if source:
                        logger.info(f"STEP 5.{filter_name}: Fetching dynamic options from {source}")
                        raw_options = await self._get_dynamic_options(db_methods, source)
                        normalized_options = self._normalize_and_deduplicate_options(
                            raw_options, filter_name
                        )
                        filters[filter_name]["options"] = self._add_default_option(
                            normalized_options, filter_label
                        )
                        logger.info(
                            f"STEP 5.{filter_name}: Loaded {len(normalized_options)} normalized options"
                        )
                    else:
                        filters[filter_name]["options"] = self._add_default_option([], filter_label)
                        logger.warning(
                            f"STEP 5.{filter_name}: No source specified for dynamic filter"
                        )

                elif filter_type == FILTER_TYPES["SEARCH"]:
                    placeholder = filter_def.get("placeholder", "")
                    filters[filter_name]["placeholder"] = placeholder
                    logger.info(f"STEP 5.{filter_name}: Configured search filter with placeholder")

                else:
                    logger.warning(f"STEP 5.{filter_name}: Unknown filter type: {filter_type}")

            logger.info("STEP 6: Building final response data")
            response_data = {
                "module": module,
                "filters": filters,
            }

            logger.info("STEP 7: Serializing response data")
            filter_serializer = InquiryFilterResponseSerializer()
            serialized_data = filter_serializer.dump(response_data)

            logger.info("STEP 8: Building final response")

            logger.info("STEP 9: Product filters retrieved successfully")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_data,
                message=message_variable.FILTERS_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"STEP ERROR: Validation error in get_product_filters: {exc}",
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
                f"STEP ERROR: Unexpected error in get_product_filters: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    async def _get_dynamic_options(
        self,
        db_methods: ProductFilterDatabaseMethods,
        source: str,
    ) -> list:
        """
        Fetch dynamic options from database based on source.

        Args:
            db_methods: Database methods instance
            source: Source identifier (category, sub_category, child_category)

        Returns:
            List of option dictionaries with label and value
        """
        source_method_map = {
            "category": db_methods.get_distinct_categories,
            "sub_category": db_methods.get_distinct_sub_categories,
            "child_category": db_methods.get_distinct_child_categories,
        }

        method = source_method_map.get(source)
        if method:
            return await method()
        return []

    def _normalize_and_deduplicate_options(
        self,
        options: list,
        filter_name: str,
    ) -> list:
        """
        Normalize and deduplicate filter options.

        Handles:
        - Cleaning Bitrix raw values (e.g., "Syria|;" -> "Syria")
        - Deduplicating by value
        - Removing empty/invalid entries

        Args:
            options: Raw options list from database
            filter_name: Name of the filter for logging

        Returns:
            Normalized and deduplicated options list
        """
        if not options:
            return []

        normalized = []
        seen_values = set()

        for option in options:
            if not isinstance(option, dict):
                # logger.warning(
                #     f"STEP NORMALIZE.{filter_name}: Invalid option format: {option}"
                # )
                continue

            label = option.get("label", "")
            value = option.get("value")

            if value is None:
                continue

            normalized_label = self._normalize_label(label)
            normalized_value = self._normalize_value(value)

            if not normalized_label or normalized_value is None:
                continue

            value_key = str(normalized_value)

            if value_key in seen_values:
                # logger.debug(
                #     f"STEP NORMALIZE.{filter_name}: Skipping duplicate value: {normalized_value}"
                # )
                continue

            seen_values.add(value_key)
            normalized.append(
                {
                    "label": normalized_label,
                    "value": normalized_value,
                }
            )

        # logger.info(
        #     f"STEP NORMALIZE.{filter_name}: Normalized {len(options)} -> {len(normalized)} options"
        # )

        return normalized

    def _normalize_label(self, label: str) -> str:
        """
        Normalize label by cleaning Bitrix raw values.

        Args:
            label: Raw label string

        Returns:
            Cleaned label string
        """
        if not label or not isinstance(label, str):
            return ""

        cleaned = label.strip()

        if "|" in cleaned:
            cleaned = cleaned.split("|")[0].strip()

        if ";" in cleaned:
            cleaned = cleaned.split(";")[0].strip()

        return cleaned

    def _normalize_value(self, value):
        """
        Normalize value by cleaning and converting.

        Args:
            value: Raw value (can be string, int, etc.)

        Returns:
            Normalized value (string or int)
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return int(value) if isinstance(value, float) and value.is_integer() else value

        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None

            if "|" in cleaned:
                cleaned = cleaned.split("|")[0].strip()

            if ";" in cleaned:
                cleaned = cleaned.split(";")[0].strip()

            if not cleaned:
                return None

            try:
                int_val = int(cleaned)
                return int_val
            except ValueError:
                return cleaned

        return str(value) if value else None

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
                isinstance(opt.get("label"), str) and opt.get("label", "").lower().startswith("all")
            )
        ]

        return [default_option] + filtered_options
