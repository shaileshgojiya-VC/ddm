"""
API views/endpoints for filter management.

Provides endpoints to retrieve filter configurations
for different modules.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.api_filters.services.inquiry_filter_service import (
    InquiryFilterService,
)
from apps.v1.api.api_filters.services.supplier_filter_service import (
    SupplierFilterService,
)
from apps.v1.api.api_filters.services.product_filter_service import (
    ProductFilterService,
)
from apps.v1.api.api_filters.services.user_filter_service import (
    UserFilterService,
)
from apps.v1.api.api_filters.services.dashboard_filter_service import (
    DashboardFilterService,
)
from apps.v1.api.api_filters.registry import FILTER_REGISTRY
from apps.v1.api.auth.models.attribute import Status
from config.db_config import get_async_db
from core.utils import constant_variable, message_variable
from core.utils.auth_dependencies import get_current_user, security
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/filters", tags=["Filters"])


@router.get("")
async def get_filters(
    module: str = Query(
        ...,
        description="Module name to fetch filters for (e.g., 'inquiry-management', 'supplier-management')",
        min_length=1,
    ),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get filters for a specific module.

    Retrieves filter configuration with populated options for the specified module.
    Supports static filters (from registry), dynamic filters (from database),
    search filters, and date range filters.

    Args:
        module: Module name (e.g., 'inquiry-management', 'supplier-management')
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session

    Returns:
        StandardResponse with filter configuration and options

    Example:
        GET /v1/filters?module=inquiry-management
        GET /v1/filters?module=supplier-management
    """
    try:
        logger.info("STEP 1: Starting get_filters endpoint")

        logger.info("STEP 2: Authenticating user")

        # Get current authenticated user
        current_user = await get_current_user(authorize, db)

        logger.info(f"STEP 3: User authenticated: {current_user.email}")

        logger.info("STEP 4: Verifying user status")

        # Verify user has active status
        if current_user.status != Status.ACTIVE:
            logger.error(f"User {current_user.email} is not active")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        logger.info(f"STEP 5: Module requested: {module}")

        # Strip whitespace from module parameter
        module = module.strip()

        logger.info("STEP 6: Validating module")

        # Validate module exists in registry
        if module not in FILTER_REGISTRY:
            logger.error(f"Invalid module requested: {module}")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.INVALID_MODULE,
            ).make

        logger.info("STEP 7: Routing to appropriate filter service")

        # Route to appropriate service based on module
        if module == "inquiry-management":
            inquiry_filter_service = InquiryFilterService()
            return await inquiry_filter_service.get_inquiry_filters(
                db=db,
                module=module,
            )
        elif module == "supplier-management":
            supplier_filter_service = SupplierFilterService()
            return await supplier_filter_service.get_supplier_filters(
                db=db,
                module=module,
            )
        elif module == "product-management":
            product_filter_service = ProductFilterService()
            return await product_filter_service.get_product_filters(
                db=db,
                module=module,
            )
        elif module == "users-management":
            user_filter_service = UserFilterService()
            return await user_filter_service.get_user_filters(
                db=db,
                module=module,
            )
        elif module == "dashboard-management":
            dashboard_filter_service = DashboardFilterService()
            return await dashboard_filter_service.get_dashboard_filters(
                db=db,
                module=module,
            )
        else:
            # For unknown modules, use inquiry service as default
            logger.info(f"STEP 7: Using inquiry filter service for module: {module}")
            inquiry_filter_service = InquiryFilterService()
            return await inquiry_filter_service.get_inquiry_filters(
                db=db,
                module=module,
            )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            f"STEP ERROR: Unexpected error in get_filters endpoint: {exc}",
            exc_info=True,
        )
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make
