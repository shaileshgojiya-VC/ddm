"""
List users service for retrieving paginated list of users.
"""

import logging
import math

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.schema import ListUsersQueryParams
from apps.v1.api.auth.serializer import UserListItemSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ListUsersService:
    """
    Service to list users with filters and pagination.
    """

    def __init__(self):
        self.user_serializer = UserListItemSerializer()

    async def list_users(
        self,
        db: AsyncSession,
        query_params: ListUsersQueryParams,
        current_user: Users,
    ):
        """
        List users with filters and pagination service method.

        Args:
            db: Database session
            query_params: Query parameters for filtering and pagination
            current_user: Currently authenticated user

        Returns:
            StandardResponse with paginated user list
        """
        try:
            logger.info("Starting list users workflow")

            # Convert role_id to int if provided
            role_id_int = None
            if query_params.role_id:
                try:
                    role_id_int = int(query_params.role_id)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid role_id format: {query_params.role_id}, ignoring filter"
                    )

            logger.info(
                f"Applying filters - role_id: {role_id_int}, status: {query_params.status}, search: {query_params.search}"
            )

            base_method = UserAuthMethod(Users)

            # Fetch users with filters and pagination
            users, total = await base_method.list_users(
                db=db,
                role_id=role_id_int,
                status_filter=query_params.status,
                search=query_params.search,
                page=query_params.page,
                limit=query_params.limit,
            )

            logger.info(f"Found {len(users)} users (total: {total})")

            logger.info("Serializing user data")

            # Prepare response data
            serialized_users = []

            for user in users:
                # Convert role object to dict with id field
                role_dict = None
                if user.role:
                    # Convert module IDs to module names
                    module_ids = user.role.module_list or []
                    module_names = await base_method.get_module_names_by_ids(
                        db=db, module_ids=module_ids
                    )

                    role_dict = {
                        "id": str(user.role.id),
                        "name": user.role.name,
                        "description": user.role.description or "",
                        "module_list": module_names,
                    }

                # Format created_by user if exists
                created_by_user = None
                if user.creator:
                    created_by_user = {
                        "id": str(user.creator.id),
                        "name": user.creator.name,
                        "email": user.creator.email,
                        "role": None,  # Don't load role for created_by user
                        "status": (
                            user.creator.status.value
                            if isinstance(user.creator.status, Status)
                            else str(user.creator.status)
                        ),
                        "created_at": user.creator.created_at,
                        "updated_at": user.creator.updated_at,
                    }

                user_response_data = {
                    "id": str(user.id),
                    "name": user.name,
                    "email": user.email,
                    "role": role_dict,
                    "status": (
                        user.status.value if isinstance(user.status, Status) else str(user.status)
                    ),
                    "created_by": created_by_user,
                    "joined_at": user.joined_at,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                }

                try:
                    serialized_user = self.user_serializer.dump(user_response_data)
                    serialized_users.append(serialized_user)
                except Exception as serialization_error:
                    logger.error(
                        f"Serialization error for user {user.email}: {serialization_error}",
                        exc_info=True,
                    )
                    # Continue with other users even if one fails

            logger.info(f"Serialized {len(serialized_users)} users")

            # Calculate pagination metadata
            total_pages = math.ceil(total / query_params.limit) if query_params.limit > 0 else 0

            pagination_data = {
                "page": query_params.page,
                "limit": query_params.limit,
                "total": total,
                "pages": total_pages,
            }

            response_data = {
                "items": serialized_users,
                "active_counts": {
                    "admin": await base_method.count_active_users_by_role(db, "admin"),
                    "management": await base_method.count_active_users_by_role(db, "management"),
                    "sales": await base_method.count_active_users_by_role(db, "sales"),
                },
            }

            logger.info("List users successful")

            content = {
                "status": constant_variable.STATUS_SUCCESS,
                "pagination": pagination_data,
                "data": response_data,
                "message": message_variable.USERS_RETRIEVED_SUCCESS,
            }

            return JSONResponse(content=content, status_code=status.HTTP_200_OK)

        except ValueError as exc:
            logger.error(
                f"Validation error in list_users_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=str(exc),
            ).make
        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in list_users_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
        except Exception as exc:
            logger.error(
                f"Unexpected error in list_users_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
