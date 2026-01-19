"""
Authentication dependencies for FastAPI endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from config.db_config import get_async_db
from core.utils.jwt_hanlder import jwt_handler
import logging

logger = logging.getLogger(__name__)

# OAuth2 scheme setup
security = HTTPBearer()


async def get_current_user(
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        authorize: HTTPAuthorizationCredentials from request header
        db: Database session

    Returns:
        Users: Current authenticated user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        logger.info("STEP 1: Extracting token from authorization header")

        token = authorize.credentials

        logger.info("STEP 2: Verifying JWT token")

        # Verify and decode token
        payload = jwt_handler.verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            logger.error("Token does not contain user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no user_id found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"STEP 3: Fetching user from database: {user_id}")

        # Convert user_id to integer for database query
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: invalid user_id format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Fetch user from database with role eagerly loaded to avoid lazy-load IO
        stmt = (
            select(Users).options(selectinload(Users.role)).where(Users.id == user_id_int).limit(1)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User not found with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"STEP 4: User authenticated successfully: {user.email}")

        return user

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in get_current_user: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def check_permission(permission_name: str):
    """
    Dependency factory to check if current user has a specific permission based on role.
    Uses role-based access control similar to management/sales pattern.

    Args:
        permission_name: Name of the permission to check (e.g., 'product_read', 'supplier_create')

    Returns:
        Dependency function that checks permission and returns user if authorized

    Usage:
        @router.get("/product")
        async def get_product(
            current_user: Users = Depends(check_permission("product_read")),
            db: AsyncSession = Depends(get_async_db),
        ):
            ...
    """
    # Map permission names to allowed roles
    # Management and admin have access to everything
    PERMISSION_ROLE_MAP = {
        # Product permissions
        "product_read": {"management", "sales", "staff", "admin"},
        "product_create": {"management", "admin"},
        "product_update": {"management", "admin"},
        "product_delete": {"management", "admin"},
        "product_category_read": {"management", "sales", "staff", "admin"},
        # Supplier permissions
        "supplier_read": {"management", "sales", "staff", "admin"},
        "supplier_create": {"management", "admin"},
        "supplier_update": {"management", "admin"},
        "supplier_delete": {"management", "admin"},
        # Default: management and admin have access to everything
    }

    async def permission_checker(
        current_user: Users = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db),
    ) -> Users:
        """
        Check if user's role has the required permission based on role name.

        Args:
            current_user: Current authenticated user
            db: Database session

        Returns:
            Users: Current user if permission check passes

        Raises:
            HTTPException: If user doesn't have the required permission
        """
        try:
            if not current_user.role_id:
                logger.error(f"User {current_user.email} has no role assigned")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: No role assigned",
                )

            # Get role name from the user's role relationship
            role_name = getattr(getattr(current_user, "role", None), "name", None)

            if not role_name:
                logger.error(f"User {current_user.email} has no role name")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Invalid role",
                )

            role_name_lower = role_name.lower()

            logger.info(
                f"Checking permission '{permission_name}' for user {current_user.email} "
                f"with role '{role_name}'"
            )

            # Management and admin have access to everything
            if role_name_lower in {"management", "admin"}:
                logger.info(
                    f"Permission check passed: User {current_user.email} with role '{role_name}' "
                    f"has access to '{permission_name}' (management/admin access)"
                )
                return current_user

            # Check if permission is in the map
            allowed_roles = PERMISSION_ROLE_MAP.get(permission_name)

            if allowed_roles and role_name_lower in allowed_roles:
                logger.info(
                    f"Permission check passed: User {current_user.email} with role '{role_name}' "
                    f"has permission '{permission_name}'"
                )
                return current_user

            # If permission not in map, deny access (except for management/admin which we already checked)
            logger.warning(
                f"User {current_user.email} (role: {role_name}) "
                f"does not have permission '{permission_name}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Permission '{permission_name}' required",
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                f"Error checking permission '{permission_name}': {exc}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Could not verify permissions",
            )

    return permission_checker
