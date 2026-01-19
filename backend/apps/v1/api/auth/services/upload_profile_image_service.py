"""
Upload profile image service for uploading user profile images.
"""

import logging
import mimetypes
import uuid
from datetime import datetime
from fastapi import UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Action
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import ActivityLog, Modules, Users
from apps.v1.api.auth.serializer import ProfileUpdateSerializer
from config.env_config import get_settings
from core.azure.azure_blob import AzureBlobService
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

settings = get_settings()
logger = logging.getLogger(__name__)


class UploadProfileImageService:
    """
    Service to upload profile images for current user.
    """

    def __init__(self):
        self.azure_blob_service = AzureBlobService()
        self.allowed_extensions = set(constant_variable.PROFILE_IMAGE_ALLOWED_EXTENSIONS)
        self.max_file_size = constant_variable.PROFILE_IMAGE_MAX_SIZE

    def _get_file_extension(self, filename: str) -> str:
        """Extect file extension from filename."""
        if not filename:
            return ""
        return filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    def _is_allowed_image(self, filename: str) -> bool:
        """Check if file extension is allowed for images."""
        extension = self._get_file_extension(filename)
        return f".{extension}" in self.allowed_extensions if extension else False

    def _detect_content_type(self, filename: str, file_content: bytes) -> str:
        """Detect MIME type from filename and content."""
        # First try mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        
        if content_type:
            return content_type
        
        # Fallback: detect from file signature
        if file_content:
            if file_content.startswith(b"\x89PNG"):
                return "image/png"
            elif file_content.startswith(b"\xff\xd8\xff"):
                return "image/jpeg"
            elif file_content.startswith(b"GIF"):
                return "image/gif"
            elif file_content.startswith(b"RIFF") and b"WEBP" in file_content[:20]:
                return "image/webp"
        
        return "image/jpeg"  # Default fallback

    def _generate_blob_path(self, user_id: int, filename: str) -> str:
        """
        Generate Azure Blob Storage path for profile image.
        
        Format: uploads/avatars/{user_id}/profile_{timestamp}_{uuid}{extension}
        """
        extension = self._get_file_extension(filename)
        file_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"uploads/avatars/{user_id}/profile_{timestamp}_{file_id}.{extension}"

    async def _create_activity_log(
        self,
        db: AsyncSession,
        user_id: int,
        action: Action,
        description: str,
        metadata: dict | None = None,
    ) -> None:
        """
        Create activity log entry for profile image upload.
        
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
            logger.info(f"Created activity log for profile image upload (user_id: {user_id})")
        except Exception as exc:
            logger.warning(
                f"Failed to create activity log for profile image upload: {exc}",
                exc_info=True,
            )

    async def upload_profile_image(
        self,
        db: AsyncSession,
        file: UploadFile,
        current_user: Users,
    ):
        """
        Upload profile image for current user.

        Args:
            db: Database session
            file: UploadFile object from FastAPI
            current_user: Currently authenticated user

        Returns:
            StandardResponse with updated profile data including new image URL
        """
        try:
            logger.info("STEP 1: Starting profile image upload workflow")

            logger.info(f"STEP 2: Validating image file for user ID: {current_user.id}")

            # Validate filename
            if not file.filename:
                logger.error("Filename is required")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Filename is required",
                ).make

            # Validate file extension
            if not self._is_allowed_image(file.filename):
                logger.error(f"Invalid image format: {file.filename}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.PROFILE_IMAGE_INVALID_FORMAT,
                ).make

            logger.info("STEP 3: Reading file content")

            # Read file content
            try:
                file_content = await file.read()
            except Exception as exc:
                logger.error(f"Error reading file {file.filename}: {exc}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=f"Error reading file: {str(exc)}",
                ).make

            # Validate file size
            file_size = len(file_content)
            if file_size > self.max_file_size:
                logger.error(f"File size exceeds limit: {file_size} bytes")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.PROFILE_IMAGE_SIZE_EXCEEDED,
                ).make

            if file_size == 0:
                logger.error("File is empty")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="File is empty",
                ).make

            logger.info("STEP 4: Generating blob path")

            # Generate blob path
            blob_path = self._generate_blob_path(current_user.id, file.filename)

            # Detect content type
            content_type = self._detect_content_type(file.filename, file_content)

            logger.info(f"STEP 5: Uploading to Azure Blob Storage: {blob_path}")

            # Upload to Azure Blob Storage
            upload_success = await self.azure_blob_service.upload_file(
                file_content=file_content,
                blob_name=blob_path,
                content_type=content_type,
                overwrite=True,
            )

            if not upload_success:
                logger.error(f"Failed to upload image to Azure Blob Storage: {blob_path}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.PROFILE_IMAGE_UPLOAD_FAILED,
                ).make

            logger.info("STEP 6: Building image URL")

            # Build full Azure blob URL
            azure_blob_storage_url = getattr(settings, "AZURE_BLOB_STORAGE_URL", None)
            if azure_blob_storage_url:
                azure_blob_storage_url = azure_blob_storage_url.rstrip("/")
                image_url = f"{azure_blob_storage_url}/{blob_path}"
            else:
                image_url = blob_path

            logger.info("STEP 7: Updating user profile with image URL")

            # Store old image URL for activity log
            old_image_url = current_user.profile_image_url

            # Update user profile with new image URL
            base_method = UserAuthMethod(Users)
            update_data = {"profile_image_url": image_url}
            
            updated_user = await base_method.update_profile_by_user_id(
                db=db, user_id=current_user.id, update_data=update_data
            )

            if not updated_user:
                logger.error(f"Failed to update profile image URL for user ID: {current_user.id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.SOMETHING_WENT_WRONG,
                ).make

            logger.info("STEP 8: Creating activity log")

            # Create activity log
            await self._create_activity_log(
                db=db,
                user_id=current_user.id,
                action=Action.UPDATE,
                description="Profile image uploaded",
                metadata={
                    "old_image_url": old_image_url,
                    "new_image_url": image_url,
                    "file_name": file.filename,
                    "file_size": file_size,
                },
            )

            logger.info("STEP 9: Preparing response data")

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

            logger.info("STEP 10: Serializing profile data")

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

            logger.info("STEP 11: Profile image upload successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_profile,
                message=message_variable.PROFILE_IMAGE_UPLOADED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in upload_profile_image_service: {exc}",
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
                f"Database error in upload_profile_image_service: {exc}",
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
                f"Unexpected error in upload_profile_image_service: {exc}",
                exc_info=True,
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

