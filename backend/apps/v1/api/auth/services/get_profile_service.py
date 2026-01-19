"""
Get profile service for retrieving current user's profile.
"""

import logging
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.serializer import ProfileSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class GetProfileService:
    """
    Service to get current user's profile.
    """

    async def get_profile(
        self,
        db: AsyncSession,
        current_user: Users,
    ):
        """
        Get current user's profile service method.

        Args:
            db: Database session
            current_user: Currently authenticated user

        Returns:
            StandardResponse with user profile data
        """
        try:
            logger.info("STEP 1: Starting profile retrieval workflow")

            logger.info(f"STEP 2: Fetching profile for user ID: {current_user.id}")

            base_method = UserAuthMethod(Users)

            # Fetch user profile with role relationship
            user = await base_method.get_profile_by_user_id(
                db=db, user_id=current_user.id
            )

            if not user:
                logger.info(f"User not found with ID: {current_user.id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.USER_NOT_FOUND,
                ).make

            logger.info(f"STEP 3: User profile found: {user.email}")

            logger.info("STEP 4: Calculating profile completeness")

            # Calculate profile completeness
            profile_completeness = base_method.calculate_profile_completeness(user)

            logger.info("STEP 5: Preparing profile response data")

            # Prepare profile response data (exclude sensitive fields)
            profile_response_data = {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "phone_number": user.phone_number,
                "location": user.location,
                "profile_image_url": user.profile_image_url,
                "profile_completeness": profile_completeness,
                "joined_at": user.joined_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }

            logger.info("STEP 6: Serializing profile data")

            # Serialize profile data
            try:
                profile_serializer = ProfileSerializer()
                serialized_profile = profile_serializer.dump(profile_response_data)
                logger.info(f"Serialization successful for user: {user.email}")
            except ValueError as serialization_error:
                logger.error(
                    f"Serialization validation error: {serialization_error}",
                    exc_info=True,
                )
                raise
            except Exception as serialization_error:
                logger.error(
                    f"Serialization error: {serialization_error}",
                    exc_info=True,
                )
                raise

            logger.info("STEP 7: Profile retrieval successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_profile,
                message=message_variable.PROFILE_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in get_profile_service: {exc}",
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
                f"Database error in get_profile_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
        except Exception as exc:
            logger.error(
                f"Unexpected error in get_profile_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

