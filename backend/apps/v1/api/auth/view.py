"""
Authentication API views/endpoints.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import (
    AdminCreateUser,
    ChangePasswordRequest,
    ForgetPasswordRequest,
    ListUsersQueryParams,
    RefreshTokenRequest,
    ResetPasswordRequest,
    UpdateUserRequest,
    UserLoginRequest,
)
from apps.v1.api.auth.services.change_password_service import ChangePasswordService
from apps.v1.api.auth.services.create_new_user_service import CreateNewUserService
from apps.v1.api.auth.services.delete_user_service import DeleteUserService
from apps.v1.api.auth.services.forget_password_service import ForgetPasswordService
from apps.v1.api.auth.services.get_user_details_service import GetUserDetailsService
from apps.v1.api.auth.services.list_users_service import ListUsersService
from apps.v1.api.auth.services.login_service import LoginService
from apps.v1.api.auth.services.refresh_token_service import RefreshTokenService
from apps.v1.api.auth.services.reset_password import ResetPasswordService
from apps.v1.api.auth.services.update_user_service import UpdateUserService
from config.db_config import get_async_db
from core.utils import constant_variable, message_variable
from core.utils.auth_dependencies import (
    HTTPAuthorizationCredentials,
    get_current_user,
    security,
)
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix=constant_variable.API_V1_PREFIX, tags=["Authentication API"])


@router.post("/auth/login")
async def login(
    body: UserLoginRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Unified login endpoint for both admin and user authentication.
    Automatically detects user role and handles login accordingly.

    Args:
        body: Login request containing email and password
        db: Database session

    Returns:
        StandardResponse with login result and user data
    """
    login_service = LoginService()
    return await login_service.login(db=db, body=body)


@router.post("/admin/create/user")
async def create_new_user(
    body: AdminCreateUser = Body(...),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Admin create new user endpoint.

    Args:
        body: Admin create user request containing user details
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session

    Returns:
        StandardResponse with user creation result and user data
    """
    try:
        logger.info("Starting admin create user endpoint")

        # Get current authenticated user
        current_user = await get_current_user(authorize, db)

        logger.info(f"Current user authenticated: {current_user.email}")

        # Verify user has active status
        if current_user.status != Status.ACTIVE:
            logger.error(f"User {current_user.email} is not active")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        logger.info("Verifying admin authorization")

        # Load user with role relationship to check admin role
        base_method = UserAuthMethod(Users)
        current_user_with_role = await base_method.find_by_id_with_role(
            db=db, user_id=current_user.id
        )

        if not current_user_with_role:
            logger.error(f"Current user not found: {current_user.id}")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

        # Check if user has role assigned
        if not current_user_with_role.role:
            logger.error(f"User {current_user_with_role.email} has no role assigned")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        # Check if user has admin role (case-insensitive)
        if current_user_with_role.role.name.lower() != "admin":
            logger.error(
                f"User {current_user_with_role.email} with role {current_user_with_role.role.name} is not authorized to create users"
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        logger.info(f"Admin authorization verified: {current_user_with_role.email}")

        logger.info("Calling create user service")

        # Call service with current_user_with_role instead of created_by from body
        create_user_service = CreateNewUserService()
        return await create_user_service.create_new_user(
            db=db, body=body, current_user=current_user_with_role
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in create_new_user endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make


@router.get("/auth/user/{user_id}")
async def get_user_details(
    user_id: str,
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get user details endpoint.

    Args:
        user_id: ID of the user to retrieve
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session

    Returns:
        StandardResponse with user details
    """
    try:
        logger.info("Starting get user details endpoint")

        # Get current authenticated user
        current_user = await get_current_user(authorize, db)

        logger.info(f"Current user authenticated: {current_user.email}")

        # Verify user has active status
        if current_user.status != Status.ACTIVE:
            logger.error(f"User {current_user.email} is not active")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        logger.info("Calling get user details service")

        # Call service to get user details
        get_user_service = GetUserDetailsService()
        return await get_user_service.get_user_details(db=db, user_id=user_id)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in get_user_details endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make


@router.get("/auth/users")
async def list_users(
    role_id: str = Query(None, description="Filter by role ID"),
    status_filter: str = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: str = Query(None, description="Search by name or email"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List users endpoint with pagination and filters.

    Args:
        role_id: Filter by role ID
        status_filter: Filter by status (active, inactive, pending, deleted)
        page: Page number for pagination
        limit: Number of items per page
        search: Search by name or email
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session

    Returns:
        StandardResponse with paginated user list
    """
    try:
        logger.info("Starting list users endpoint")

        # Get current authenticated user
        current_user = await get_current_user(authorize, db)

        logger.info(f"Current user authenticated: {current_user.email}")

        # Verify user has active status
        if current_user.status != Status.ACTIVE:
            logger.error(f"User {current_user.email} is not active")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        logger.info("Building query parameters")

        # Build query parameters object
        query_params = ListUsersQueryParams(
            role_id=role_id,
            status=status_filter,
            page=page,
            limit=limit,
            search=search,
        )

        logger.info("Calling list users service")

        # Call service to list users
        list_users_service = ListUsersService()
        return await list_users_service.list_users(
            db=db, query_params=query_params, current_user=current_user
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in list_users endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make


@router.put("/auth/user/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest = Body(...),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update user endpoint.

    Args:
        user_id: ID of the user to update
        body: Update user request containing fields to update
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session

    Returns:
        StandardResponse with updated user details
    """
    try:
        logger.info("Starting update user endpoint")

        # Get current authenticated user
        current_user = await get_current_user(authorize, db)

        logger.info(f"Current user authenticated: {current_user.email}")

        # Verify user has active status
        if current_user.status != Status.ACTIVE:
            logger.error(f"User {current_user.email} is not active")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        logger.info("Calling update user service")

        # Call service to update user
        update_user_service = UpdateUserService()
        return await update_user_service.update_user(
            db=db, user_id=user_id, body=body, current_user=current_user
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in update_user endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make


@router.delete("/auth/user/{user_id}")
async def delete_user(
    user_id: str,
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete user endpoint (soft delete).

    Args:
        user_id: ID of the user to delete
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session

    Returns:
        StandardResponse with deletion result
    """
    try:
        logger.info("Starting delete user endpoint")

        # Get current authenticated user
        current_user = await get_current_user(authorize, db)

        logger.info(f"Current user authenticated: {current_user.email}")

        # Verify user has active status
        if current_user.status != Status.ACTIVE:
            logger.error(f"User {current_user.email} is not active")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        logger.info("Calling delete user service")

        # Call service to delete user
        delete_user_service = DeleteUserService()
        return await delete_user_service.delete_user(
            db=db, user_id=user_id, current_user=current_user
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in delete_user endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make


@router.post("/auth/password/forget")
async def forget_password(
    body: ForgetPasswordRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Forget password endpoint.

    Args:
        body: Forget password request containing email
        db: Database session

    Returns:
        StandardResponse with reset token information
    """
    try:
        logger.info("Starting forget password endpoint")

        logger.info("Calling forget password service")

        # Call service to handle forget password
        forget_password_service = ForgetPasswordService()
        return await forget_password_service.forget_password(db=db, body=body)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in forget_password endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make


@router.post("/auth/password/reset")
async def reset_password(
    body: ResetPasswordRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Reset password endpoint using reset token.

    Args:
        body: Reset password request containing token and new password
        db: Database session

    Returns:
        StandardResponse with reset result
    """
    try:
        logger.info("Starting reset password endpoint")

        logger.info("Calling reset password service")

        # Call service to handle password reset
        reset_password_service = ResetPasswordService()
        return await reset_password_service.reset_password(db=db, body=body)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in reset_password endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make


@router.post("/auth/password/change")
async def change_password(
    body: ChangePasswordRequest = Body(...),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Change password endpoint.

    Args:
        body: Change password request containing current_password, new_password, confirm_password
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session

    Returns:
        StandardResponse with new access token and user data
    """
    try:
        logger.info("Starting change password endpoint")

        # Get current authenticated user
        current_user = await get_current_user(authorize, db)

        logger.info(f"Current user authenticated: {current_user.email}")

        # Verify user has active or pending status (pending users need to change password)
        if current_user.status not in [Status.ACTIVE, Status.PENDING]:
            logger.error(f"User {current_user.email} status is {current_user.status}")
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_403_FORBIDDEN,
                data=constant_variable.STATUS_NULL,
                message=message_variable.UNAUTHORIZED,
            ).make

        logger.info("Calling change password service")

        # Call service to change password
        change_password_service = ChangePasswordService()
        return await change_password_service.change_password(
            db=db, body=body, current_user=current_user
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in change_password endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make


@router.post("/auth/refresh")
async def refresh_token(
    body: RefreshTokenRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Refresh token endpoint.

    Args:
        body: Refresh token request containing refresh_token
        db: Database session

    Returns:
        StandardResponse with new access and refresh tokens
    """
    try:
        logger.info("Starting refresh token endpoint")

        logger.info("Calling refresh token service")

        # Call service to refresh token
        refresh_token_service = RefreshTokenService()
        return await refresh_token_service.refresh_token(db=db, body=body)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in refresh_token endpoint: {exc}", exc_info=True)
        return StandardResponse(
            status=constant_variable.STATUS_FAIL,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=constant_variable.STATUS_NULL,
            message=message_variable.SOMETHING_WENT_WRONG,
        ).make
