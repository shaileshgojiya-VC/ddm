"""
Update profile service for updating current user's profile.
"""

import logging
import re
from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Action
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import ActivityLog, Modules, Users
from apps.v1.api.auth.schema import UpdateProfileRequest
from apps.v1.api.auth.serializer import ProfileUpdateSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class UpdateProfileService:
    """
    Service to update current user's profile.
    """

    def __init__(self):
        self.allowed_fields = constant_variable.PROFILE_FIELDS_ALLOWED_FOR_UPDATE
        self.restricted_fields = constant_variable.PROFILE_FIELDS_RESTRICTED

    def _validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone_number: Phone number string
            
        Returns:
            True if valid, False otherwise
        """
        if not phone_number:
            return True  # Optional field
        
        # Remove spaces, dashes, parentheses, and plus sign for validation
        cleaned = re.sub(r"[\s\-\(\)\+]", "", phone_number)
        
        # Check if remaining characters are digits
        if not cleaned.isdigit():
            return False
        
        # Check length (10-20 digits after cleaning)
        length = len(cleaned)
        return constant_variable.PROFILE_PHONE_MIN_LENGTH <= length <= constant_variable.PROFILE_PHONE_MAX_LENGTH

    def _sanitize_string(self, value: str, max_length: int) -> str:
        """
        Sanitize string input by trimming and limiting length.
        
        Args:
            value: String value to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not value:
            return value
        
        # Trim whitespace
        sanitized = value.strip()
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized

    def _validate_and_sanitize_update_data(
        self, body: UpdateProfileRequest
    ) -> tuple[dict, str | None]:
        """
        Validate and sanitize update data.
        
        Args:
            body: Update profile request
            
        Returns:
            Tuple of (update_data dict, error_message or None)
        """
        update_data = {}
        
        # Validate and sanitize name
        if body.name is not None:
            if not body.name.strip():
                return {}, "Name cannot be empty"
            sanitized_name = self._sanitize_string(
                body.name, constant_variable.PROFILE_NAME_MAX_LENGTH
            )
            update_data["name"] = sanitized_name
        
        # Validate and sanitize phone_number
        if body.phone_number is not None:
            if body.phone_number.strip():
                if not self._validate_phone_number(body.phone_number):
                    return {}, message_variable.PROFILE_PHONE_INVALID_FORMAT
                update_data["phone_number"] = body.phone_number.strip()
            else:
                # Allow setting to None/empty
                update_data["phone_number"] = None
        
        # Validate and sanitize location
        if body.location is not None:
            if body.location.strip():
                sanitized_location = self._sanitize_string(
                    body.location, constant_variable.PROFILE_LOCATION_MAX_LENGTH
                )
                update_data["location"] = sanitized_location
            else:
                # Allow setting to None/empty
                update_data["location"] = None
        
        return update_data, None

    async def _create_activity_log(
        self,
        db: AsyncSession,
        user_id: int,
        action: Action,
        description: str,
        metadata: dict | None = None,
    ) -> None:
        """
        Create activity log entry for profile update.
        
        Args:
            db: Database session
            user_id: User ID
            action: Action type
            description: Description of the activity
            metadata: Optional metadata
        """
        try:
            # Get auth module ID
            stmt = select(Modules).where(Modules.slug == "auth")
            result = await db.execute(stmt)
            module = result.scalar_one_or_none()
            
            if not module:
                logger.warning("Auth module not found, skipping activity log")
                return
            
            activity_log = ActivityLog(
                user_id=user_id,
                module_id=module.id,
                action=action,
                entity_id=str(user_id),
                description=description,
                activity_metadata=metadata,
            )
            
            db.add(activity_log)
            await db.flush()
            logger.info(f"Created activity log for profile update (user_id: {user_id})")
        except Exception as exc:
            logger.warning(
                f"Failed to create activity log for profile update: {exc}",
                exc_info=True,
            )

    async def update_profile(
        self,
        db: AsyncSession,
        body: UpdateProfileRequest,
        current_user: Users,
    ):
        """
        Update current user's profile service method.

        Args:
            db: Database session
            body: Update profile request containing fields to update
            current_user: Currently authenticated user

        Returns:
            StandardResponse with updated profile details
        """
        try:
            logger.info("STEP 1: Starting profile update workflow")

            logger.info(f"STEP 2: Validating update data for user ID: {current_user.id}")

            # Validate and sanitize update data
            update_data, error_message = self._validate_and_sanitize_update_data(body)
            
            if error_message:
                logger.error(f"Validation error: {error_message}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    data=constant_variable.STATUS_NULL,
                    message=error_message,
                ).make

            if not update_data:
                logger.info("No fields provided for update")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.PROFILE_UPDATE_NO_FIELDS,
                ).make

            logger.info(f"STEP 3: Updating profile with data: {update_data}")

            base_method = UserAuthMethod(Users)

            # Store old values for activity log
            old_values = {
                "name": current_user.name,
                "phone_number": current_user.phone_number,
                "location": current_user.location,
            }

            # Update user profile
            updated_user = await base_method.update_profile_by_user_id(
                db=db, user_id=current_user.id, update_data=update_data
            )

            if not updated_user:
                logger.error(f"Failed to update profile for user ID: {current_user.id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("STEP 4: Profile updated successfully")

            # Create activity log
            changed_fields = {
                field: {"old": old_values.get(field), "new": update_data.get(field)}
                for field in update_data.keys()
            }
            
            await self._create_activity_log(
                db=db,
                user_id=current_user.id,
                action=Action.UPDATE,
                description=f"Profile updated: {', '.join(update_data.keys())}",
                metadata={"changed_fields": changed_fields},
            )

            logger.info("STEP 5: Preparing response data")

            # Prepare response data
            profile_response_data = {
                "id": str(updated_user.id),
                "name": updated_user.name,
                "email": updated_user.email,
                "phone_number": updated_user.phone_number,
                "location": updated_user.location,
                "profile_image_url": updated_user.profile_image_url,
                "updated_at": updated_user.updated_at,
            }

            logger.info("STEP 6: Serializing updated profile data")

            # Serialize profile data
            try:
                profile_serializer = ProfileUpdateSerializer()
                serialized_profile = profile_serializer.dump(profile_response_data)
                logger.info(f"Serialization successful for user: {updated_user.email}")
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

            logger.info("STEP 7: Profile update successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_profile,
                message=message_variable.PROFILE_UPDATED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in update_profile_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=str(exc),
            ).make
        except SQLAlchemyError as exc:
            logger.error(
                f"Database error in update_profile_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
        except Exception as exc:
            logger.error(
                f"Unexpected error in update_profile_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

