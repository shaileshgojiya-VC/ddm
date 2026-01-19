"""
Role API views/endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.role.services.list_role_service import ListRoleService
from apps.v1.api.role.schema import ListRolesQueryParams
from config.db_config import get_async_db
from core.utils import constant_variable, message_variable
from core.utils.auth_dependencies import get_current_user, security
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth/roles", tags=["Role API"])


@router.get("")
async def list_roles(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: str = Query(None, description="Search by name or description"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List roles endpoint with pagination and search.

    Args:
        page: Page number for pagination
        limit: Number of items per page
        search: Search by name or description
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session

    Returns:
        StandardResponse with paginated role list
    """
    try:
        logger.info("STEP 1: Starting list roles endpoint")

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

        logger.info("STEP 5: Building query parameters")

        # Build query parameters object
        query_params = ListRolesQueryParams(
            page=page,
            limit=limit,
            search=search,
        )

        logger.info("STEP 6: Calling list roles service")

        # Call service to list roles
        list_roles_service = ListRoleService()
        return await list_roles_service.list_roles(
            db=db, query_params=query_params, current_user=current_user
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in list_roles endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make
