"""
Service for retrieving inquiry management filters.

This service handles the business logic for fetching and populating
filter options for the inquiry-management module.

Filter Type Responsibilities:
- static/dynamic: Returns options array (dropdown filters)
- search: Returns placeholder only (text input)
- date_range: Returns min_date and max_date only (date picker)

All filters include normalization and deduplication for clean UI consumption.
"""

import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.api_filters.models.method import InquiryFilterDatabaseMethods
from apps.v1.api.api_filters.registry import (
    FILTER_REGISTRY,
    FILTER_TYPES,
    STATIC_OPTIONS,
)
from apps.v1.api.api_filters.serilizer import InquiryFilterResponseSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class InquiryFilterService:
    """
    Service class for retrieving inquiry management filters.

    Provides business logic for fetching filter configurations
    and populating options from static sources and database.

    Key Features:
    - Type-specific field inclusion (only relevant fields per filter type)
    - Normalization of Bitrix raw values (e.g., "Syria|;" -> "Syria")
    - Deduplication by value
    - Clean, UI-friendly response structure
    """

    async def get_inquiry_filters(
        self,
        db: AsyncSession,
        module: str,
    ):
        """
        Retrieve filters for inquiry-management module with populated options.

        Args:
            db: Database session
            module: Module name (should be 'inquiry-management')

        Returns:
            StandardResponse with filter configuration and options
        """
        try:
            logger.info("STEP 1: Starting inquiry filter retrieval workflow")

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
            db_methods = InquiryFilterDatabaseMethods(db)

            logger.info("STEP 5: Fetching all filters in a single database call")
            all_filters_data = await db_methods.get_all_filters()

            logger.info("STEP 6: Building filters with type-specific fields")
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
                    f"STEP 6.{filter_name}: Processing {filter_name} filter (type: {filter_type})"
                )

                if filter_type == FILTER_TYPES["STATIC"]:
                    options_key = filter_def.get("options_key")
                    if options_key and options_key in STATIC_OPTIONS:
                        static_options = STATIC_OPTIONS[options_key]
                        filters[filter_name]["options"] = self._add_default_option(
                            static_options, filter_label
                        )
                        logger.info(
                            f"STEP 6.{filter_name}: Loaded static options for {options_key}"
                        )
                    else:
                        filters[filter_name]["options"] = self._add_default_option([], filter_label)
                        logger.warning(
                            f"STEP 6.{filter_name}: No static options found for {options_key}"
                        )

                elif filter_type == FILTER_TYPES["DYNAMIC"]:
                    source = filter_def.get("source")
                    if source:
                        logger.info(f"STEP 6.{filter_name}: Using pre-fetched dynamic options from {source}")
                        raw_options = self._get_prefetched_options(all_filters_data, source)
                        
                        # Special handling for stages - already grouped by phase
                        is_stage_filter = (filter_name == "stage_id" and source == "stages")
                        logger.info(f"STEP 6.{filter_name}: is_stage_filter={is_stage_filter}, filter_name={filter_name}, source={source}")
                        
                        if is_stage_filter:
                            logger.info(f"STEP 6.{filter_name}: Using pre-grouped stages by phase")
                            grouped_stages = all_filters_data.get("stages", {})
                            # Transform grouped stages dictionary into array format
                            groups_array = self._transform_stages_to_grouped_array(grouped_stages)
                            total_stages = sum(len(group.get("items", [])) for group in groups_array)
                            
                            filters[filter_name]["grouped"] = True
                            filters[filter_name]["groups"] = groups_array
                            filters[filter_name]["total_options"] = total_stages
                            logger.info(
                                f"STEP 6.{filter_name}: Loaded {total_stages} stages in {len(groups_array)} groups"
                            )
                        else:
                            normalized_options = self._normalize_and_deduplicate_options(
                                raw_options, filter_name
                            )
                            options_with_default = self._add_default_option(
                                normalized_options, filter_label
                            )
                            filters[filter_name]["options"] = options_with_default
                            filters[filter_name]["total_options"] = len(normalized_options)
                            logger.info(
                                f"STEP 6.{filter_name}: Loaded {len(normalized_options)} normalized options"
                            )
                    else:
                        filters[filter_name]["options"] = self._add_default_option([], filter_label)
                        logger.warning(
                            f"STEP 6.{filter_name}: No source specified for dynamic filter"
                        )

                elif filter_type == FILTER_TYPES["SEARCH"]:
                    placeholder = filter_def.get("placeholder", "")
                    filters[filter_name]["placeholder"] = placeholder
                    logger.info(f"STEP 6.{filter_name}: Configured search filter with placeholder")

                elif filter_type == FILTER_TYPES["DATE_RANGE"]:
                    logger.info(f"STEP 6.{filter_name}: Using pre-fetched date range metadata")
                    date_range_data = all_filters_data.get("date_range", {})
                    filters[filter_name]["min_date"] = date_range_data.get("min_date")
                    filters[filter_name]["max_date"] = date_range_data.get("max_date")
                    logger.info(f"STEP 6.{filter_name}: Date range configured: {date_range_data}")

                else:
                    logger.warning(f"STEP 6.{filter_name}: Unknown filter type: {filter_type}")

            logger.info("STEP 7: Building final response data")
            response_data = {
                "module": module,
                "filters": filters,
            }

            logger.info("STEP 8: Serializing response data")
            filter_serializer = InquiryFilterResponseSerializer()
            serialized_data = filter_serializer.dump(response_data)

            logger.info("STEP 9: Building final response")

            logger.info("STEP 10: Inquiry filters retrieved successfully")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_data,
                message=message_variable.FILTERS_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"STEP ERROR: Validation error in get_inquiry_filters: {exc}",
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
                f"STEP ERROR: Unexpected error in get_inquiry_filters: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    def _get_prefetched_options(
        self,
        all_filters_data: dict,
        source: str,
    ) -> list:
        """
        Get dynamic options from pre-fetched all filters data.

        Args:
            all_filters_data: Dictionary containing all pre-fetched filter data
            source: Source identifier (stages, assignees, country, etc.)

        Returns:
            List of option dictionaries with label and value
        """
        source_map = {
            "stages": "stages",
            "assignees": "assignees",
            "country": "countries",
            "customer_id": "customers",
            "product_id": "products",
        }

        data_key = source_map.get(source)
        if data_key:
            data = all_filters_data.get(data_key, [])
            # If stages, flatten the grouped structure
            if data_key == "stages" and isinstance(data, dict):
                flattened = []
                for phase_stages in data.values():
                    flattened.extend(phase_stages)
                return flattened
            return data if isinstance(data, list) else []
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

        Examples:
        - "Syria|;" -> "Syria"
        - "Libya|;|42662" -> "Libya"
        - "Bruno Conte" -> "Bruno Conte"

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

        Handles Bitrix format strings (e.g., "United Kingdom|54.7023545;-3.2765753|23732")
        and extracts just the clean value.

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

            # Clean Bitrix format: "Country|coordinates|id" -> "Country"
            if "|" in cleaned:
                cleaned = cleaned.split("|")[0].strip()

            if ";" in cleaned:
                cleaned = cleaned.split(";")[0].strip()

            if not cleaned:
                return None

            # Try to convert to int if it's a pure number
            try:
                int_val = int(cleaned)
                return int_val
            except ValueError:
                return cleaned

        return str(value) if value else None

    def _transform_stages_to_grouped_array(
        self,
        grouped_stages: dict,
    ) -> list:
        """
        Transform grouped stages dictionary into array format with group metadata.

        Args:
            grouped_stages: Dictionary with phase keys and stage lists

        Returns:
            List of group objects with group_key, group_label, order_sequence, and items
        """
        # Phase order mapping (for group order_sequence)
        phase_order_map = {
            "LEAD": 1,
            "REGISTRATION": 2,
            "DEAL": 3,
        }

        # Phase label mapping (for display names)
        phase_label_map = {
            "LEAD": "Lead",
            "REGISTRATION": "Registration",
            "DEAL": "Deal",
        }

        groups_array = []

        for phase_key, stage_list in grouped_stages.items():
            # Skip empty groups
            if not stage_list:
                continue

            # Transform stages to items (remove order_sequence from items)
            # Sort by order_sequence to ensure correct order
            sorted_stages = sorted(
                stage_list,
                key=lambda s: s.get("order_sequence", 0)
            )
            
            items = [
                {
                    "label": stage.get("label", ""),
                    "value": stage.get("value"),
                }
                for stage in sorted_stages
                if stage.get("label") and stage.get("value") is not None
            ]

            # Skip groups with no valid items
            if not items:
                continue

            # Create group object
            group_obj = {
                "group_key": phase_key,
                "group_label": phase_label_map.get(phase_key, phase_key.title()),
                "order_sequence": phase_order_map.get(phase_key, 0),
                "items": items,
            }

            groups_array.append(group_obj)

        # Sort groups by order_sequence
        groups_array.sort(key=lambda x: x.get("order_sequence", 0))

        return groups_array

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
