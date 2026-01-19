"""
List roles service for retrieving paginated list of roles.
"""

import logging
import math

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.model import Roles, Users
from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.role.models.method.method import RoleAuthMethod
from apps.v1.api.role.schema import ListRolesQueryParams
from apps.v1.api.auth.serializer import RoleListItemSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ListRoleService:
    """
    Service to list roles with search and pagination.
    """

    async def list_roles(
        self,
        db: AsyncSession,
        query_params: ListRolesQueryParams,
        current_user: Users,
    ):
        """
        List roles with search and pagination service method.

        Args:
            db: Database session
            query_params: Query parameters for search and pagination
            current_user: Currently authenticated user

        Returns:
            StandardResponse with paginated role list
        """
        try:
            logger.info("STEP 1: Starting list roles workflow")

            logger.info("STEP 2: Applying search filter and pagination")

            base_method = RoleAuthMethod(Roles)

            roles, total = await base_method.list_roles(
                db=db,
                search=query_params.search,
                page=query_params.page,
                limit=query_params.limit,
            )

            logger.info(f"STEP 3: Found {len(roles)} roles (total: {total})")

            logger.info("STEP 4: Loading module IDs for role access")

            modules_map = await base_method.get_modules_map(db)

            logger.info("STEP 5: Serializing role data")

            serialized_roles = []
            role_serializer = RoleListItemSerializer()

            for role in roles:
                module_names = base_method.modules_for_role(role.name, modules_map)

                role_response_data = {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description or "",
                    "status": (
                        role.status.value if isinstance(role.status, Status) else str(role.status)
                    ),
                    "created_at": role.created_at,
                    "updated_at": role.updated_at,
                    "module_list": module_names,
                }

                try:
                    serialized_role = role_serializer.dump(role_response_data)
                    serialized_roles.append(serialized_role)
                except Exception as serialization_error:
                    logger.error(
                        f"Serialization error for role {role.name}: {serialization_error}",
                        exc_info=True,
                    )

            logger.info(f"STEP 6: Serialized {len(serialized_roles)} roles")

            logger.info("STEP 7: Calculating pagination metadata")

            total_pages = math.ceil(total / query_params.limit) if query_params.limit > 0 else 0

            pagination_data = {
                "page": query_params.page,
                "limit": query_params.limit,
                "total": total,
                "pages": total_pages,
            }

            response_data = {
                "items": serialized_roles,
            }

            logger.info("STEP 8: List roles successful")

            content = {
                "status": constant_variable.STATUS_SUCCESS,
                "data": response_data,
                "pagination": pagination_data,
                "message": message_variable.ROLES_RETRIEVED_SUCCESS,
            }

            return JSONResponse(content=content, status_code=status.HTTP_200_OK)

        except ValueError as exc:
            logger.error(
                f"Validation error in list_roles_service: {exc}",
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
                f"Database error in list_roles_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
