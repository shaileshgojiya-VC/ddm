"""
Get user details service for retrieving user information.
"""

import logging
from datetime import datetime

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.methods.method import UserAuthMethod
from apps.v1.api.auth.models.model import Users
from apps.v1.api.auth.serializer import InquiryItemSerializer, UserDetailsSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class GetUserDetailsService:
    """
    Service to get user details by UUID.
    """

    def __init__(self):
        self.user_serializer = UserDetailsSerializer()
        self.inquiry_serializer = InquiryItemSerializer(many=True)

    async def get_user_details(
        self,
        db: AsyncSession,
        user_id: str,
    ):
        """
        Get user details by ID service method.

        Args:
            db: Database session
            user_id: ID of the user to retrieve

        Returns:
            StandardResponse with user details
        """
        try:
            logger.info("Starting user details retrieval workflow")

            logger.info(f"Fetching user with ID: {user_id}")

            # Convert user_id (string) to int
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid user ID format: {user_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Invalid user ID format",
                ).make

            base_method = UserAuthMethod(Users)

            # Fetch user with role relationship loaded using ID
            user = await base_method.find_by_id_with_role(db=db, user_id=user_id_int)

            if not user:
                logger.info(f"User not found with ID: {user_id_int}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.USER_NOT_FOUND,
                ).make

            logger.info(f"User found: {user.email}")

            logger.info("Serializing user data")
            
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

            user_response_data = {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": role_dict,
                "phone_number": user.phone_number,
                "location": user.location,
                "profile_image_url": user.profile_image_url,
                "status": (
                    user.status.value if isinstance(user.status, Status) else str(user.status)
                ),
                "parent_id": str(user.parent_user_id) if user.parent_user_id else None,
                "created_by": user.creator,
                "joined_at": user.joined_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }

            # Serialize user data
            try:
                serialized_user = self.user_serializer.dump(user_response_data)
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

            logger.info("Fetching user inquiries")

            # Fetch inquiries assigned to user
            inquiries = await base_method.get_inquiries_by_user_id(
                db=db, user_id=user_id_int
            )

            logger.info(f"Found {len(inquiries)} inquiries for user")

            # Format inquiry data for serialization
            inquiry_data_list = []
            for inquiry in inquiries:
                # Get company name
                company_name = None
                if inquiry.company:
                    company_name = getattr(inquiry.company, "company_name", None)

                # Get customer name (from company or inquiry name)
                customer_name = company_name or inquiry.name or None

                # Get stage name from current_stage first, then from latest request_stage_activities
                stage_name = None
                if inquiry.current_stage:
                    stage_name = getattr(inquiry.current_stage, "stage_name", None)

                # If not found, get from latest request_stage_activities
                if (
                    not stage_name
                    and hasattr(inquiry, "request_stage_activities")
                    and inquiry.request_stage_activities
                ):
                    # Sort activities by created_at (descending) and order_sequence (descending) to get the latest
                    sorted_activities = sorted(
                        inquiry.request_stage_activities,
                        key=lambda a: (
                            a.created_at if a.created_at else datetime.min,
                            a.order_sequence if a.order_sequence else 0,
                        ),
                        reverse=True,
                    )

                    # Get the latest activity's stage name
                    for activity in sorted_activities:
                        if hasattr(activity, "stage") and activity.stage:
                            if activity.stage.stage_name:
                                stage_name = activity.stage.stage_name
                                break

                # Get phase value
                phase_value = None
                if inquiry.phase:
                    if hasattr(inquiry.phase, "value"):
                        phase_value = inquiry.phase.value
                    else:
                        phase_value = str(inquiry.phase)

                inquiry_data = {
                    "id": str(inquiry.id),
                    "phase": phase_value,
                    "stage": stage_name,
                    "customer_name": customer_name,
                    "company_name": company_name,
                }
                inquiry_data_list.append(inquiry_data)

            logger.info("Serializing inquiry data")

            # Serialize inquiries directly
            serialized_inquiries = self.inquiry_serializer.dump(inquiry_data_list)

            logger.info("Fetching user inquiry metrics")

            # Fetch user-specific inquiry metrics
            metrics = await base_method.fetch_user_inquiry_metrics(
                db=db, user_id=user_id_int
            )
            serialized_user.update(metrics)

            # Add inquiries to serialized user data
            serialized_user["inquiries"] = serialized_inquiries

            logger.info("User details retrieval successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_user,
                message=message_variable.USER_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in get_user_details_service: {exc}",
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
                f"Database error in get_user_details_service: {exc}",
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
                f"Unexpected error in get_user_details_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
