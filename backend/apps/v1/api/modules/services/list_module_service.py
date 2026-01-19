"""
List modules service for retrieving paginated list of modules.
"""

import logging
import math

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.modules.models.method.method import ModuleAuthMethod
from apps.v1.api.auth.models.model import Modules
from apps.v1.api.modules.schema import ListModulesQueryParams
from apps.v1.api.modules.serializer import ModuleListItemSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ListModuleService:
    """
    Service to list modules with search and pagination.
    """

    async def list_modules(
        self,
        db: AsyncSession,
        query_params: ListModulesQueryParams,
        current_user: Users,
    ):
        """
        List modules with search and pagination service method.

        Args:
            db: Database session
            query_params: Query parameters for search and pagination
            current_user: Currently authenticated user

        Returns:
            StandardResponse with paginated module list
        """
        try:
            logger.info("STEP 1: Starting list modules workflow")

            logger.info("STEP 2: Applying search filter and pagination")

            base_method = ModuleAuthMethod(Modules)

            modules, total = await base_method.list_modules(
                db=db,
                search=query_params.search,
                page=query_params.page,
                limit=query_params.limit,
            )

            logger.info(f"STEP 3: Found {len(modules)} modules (total: {total})")

            logger.info("STEP 4: Serializing module data")

            serialized_modules = []
            module_serializer = ModuleListItemSerializer()

            for module in modules:
                module_response_data = {
                    "id": str(module.id),
                    "name": module.name,
                    "slug": module.slug,
                    "description": module.description or "",
                    "status": (
                        module.status.value
                        if isinstance(module.status, Status)
                        else str(module.status)
                    ),
                    "created_at": module.created_at,
                    "updated_at": module.updated_at,
                }

                try:
                    serialized_module = module_serializer.dump(module_response_data)
                    serialized_modules.append(serialized_module)
                except Exception as serialization_error:
                    logger.error(
                        f"Serialization error for module {module.name}: {serialization_error}",
                        exc_info=True,
                    )

            logger.info(f"STEP 5: Serialized {len(serialized_modules)} modules")

            logger.info("STEP 6: Calculating pagination metadata")

            total_pages = math.ceil(total / query_params.limit) if query_params.limit > 0 else 0

            pagination_data = {
                "page": query_params.page,
                "limit": query_params.limit,
                "total": total,
                "pages": total_pages,
            }

            response_data = {
                "items": serialized_modules,
            }

            logger.info("STEP 7: List modules successful")

            content = {
                "status": constant_variable.STATUS_SUCCESS,
                "pagination": pagination_data,
                "data": response_data,
                "message": message_variable.MODULES_RETRIEVED_SUCCESS,
            }

            return JSONResponse(content=content, status_code=status.HTTP_200_OK)

        except ValueError as exc:
            logger.error(
                f"Validation error in list_modules_service: {exc}",
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
                f"Database error in list_modules_service: {exc}",
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
                f"Unexpected error in list_modules_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
