"""
Get request detail service for retrieving request information.
Refactored to use joinload/selectinload for all relationships.
"""

import logging
from typing import List, Dict, Any, Optional

from fastapi import status
from apps.v1.api.auth.models.model import Users
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.v1.api.request.models.methods.method import RequestMethod, StageMethod
from apps.v1.api.request.models.model import Requests
from apps.v1.api.products.models.model import Categories
from apps.v1.api.request.serializer import (
    RequestDetailSerializer,
    UserDetailSerializer,
    ProductDetailSerializer,
    MailCommunicationSerializer,
    DocumentDetailSerializer,
    StageTimelineSerializer,
)
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class GetRequestDetailService:
    """
    Service to get request details by UUID.
    Uses joinload/selectinload to load all relationships in a single query.
    """

    async def get_request_detail(
        self,
        db: AsyncSession,
        request_id: str,
        current_user: Users = None,
    ):
        """
        Get request details by ID service method.
        Loads all relationships using joinload/selectinload.

        Args:
            db: Database session
            request_id: ID of the request to retrieve

        Returns:
            StandardResponse with request details
        """
        try:
            logger.info("STEP 1: Starting request details retrieval workflow")

            logger.info(f"STEP 2: Fetching request with ID: {request_id}")

            base_method = RequestMethod(Requests)

            request = await base_method.find_by_id(
                db=db,
                request_id=request_id,
                current_user=current_user,
            )

            if not request:
                logger.info(f"STEP 3: Request not found with ID: {request_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message=message_variable.REQUEST_NOT_FOUND,
                ).make

            logger.info(f"STEP 3: Request found: {request.name}")

            logger.info("STEP 4: Formatting user details from loaded relationships")

            # Format user details from loaded relationships
            user_details = self._format_user_details(request)

            logger.info("STEP 5: Formatting product details from loaded relationships")

            # Format product details from request_products relationship
            product_details = await self._format_product_details(request, db)

            logger.info("STEP 6: Formatting mail communications from loaded relationships")

            # Format mail communications from loaded emails
            mail_communications = self._format_mail_communications(request)

            logger.info("STEP 7: Formatting document details from loaded relationships")

            # Format document details from loaded documents
            document_details = self._format_document_details(request)

            logger.info("STEP 8: Formatting stage timeline from loaded relationships")

            # Format stage timeline from loaded stages
            stage_timeline = await self._format_stage_timeline(request, db)

            logger.info("STEP 9: Building complete request detail response")

            # Build request detail data
            request_detail_data = self._format_request_detail_data(
                request=request,
                user_details=user_details,
                product_details=product_details,
                mail_communications=mail_communications,
                document_details=document_details,
                stage_timeline=stage_timeline,
            )

            logger.info("STEP 10: Serializing request data")

            try:
                request_serializer = RequestDetailSerializer()
                serialized_request = request_serializer.dump(request_detail_data)
                logger.info(f"STEP 11: Serialization successful for request: {request.name}")
            except ValueError as serialization_error:
                logger.error(
                    f"STEP 11: Serialization validation error: {serialization_error}",
                    exc_info=True,
                )
                raise
            except Exception as serialization_error:
                logger.error(
                    f"STEP 11: Serialization error: {serialization_error}",
                    exc_info=True,
                )
                raise

            logger.info("STEP 12: Request details retrieval successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_request,
                message=message_variable.REQUEST_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"STEP ERROR: Validation error in get_request_detail_service: {exc}",
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
                f"STEP ERROR: Database error in get_request_detail_service: {exc}",
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
                f"STEP ERROR: Unexpected error in get_request_detail_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    def _format_user_details(self, request: Requests) -> List[Dict[str, Any]]:
        """
        Format user details from loaded relationships.
        No loops used - uses list comprehensions and mapping.
        """
        user_details = []
        all_users = getattr(request, "_all_users", {})

        # Responsible user
        if request.assigned_by:
            responsible_user = all_users.get(request.assigned_by)
            if responsible_user:
                user_detail = self._format_single_user_detail(responsible_user, "responsible")
                if user_detail:
                    user_details.append(user_detail)

        # Created user
        if request.created_by:
            created_user = all_users.get(request.created_by)
            if created_user:
                user_detail = self._format_single_user_detail(created_user, "observer")
                if user_detail:
                    existing_uuids = {ud.get("id") for ud in user_details if ud.get("id")}
                    if user_detail.get("id") not in existing_uuids:
                        user_details.append(user_detail)

        # Modified user
        if request.modified_by:
            modified_user = all_users.get(request.modified_by)
            if modified_user:
                user_detail = self._format_single_user_detail(modified_user, "observer")
                if user_detail:
                    existing_ids = {ud.get("id") for ud in user_details if ud.get("id")}
                    if user_detail.get("id") not in existing_ids:
                        user_details.append(user_detail)

        # Observer users
        if request.observer_ids and isinstance(request.observer_ids, list):
            observer_users = [
                all_users.get(obs_id)
                for obs_id in request.observer_ids
                if obs_id and all_users.get(obs_id)
            ]
            observer_details = [
                self._format_single_user_detail(obs_user, "observer")
                for obs_user in observer_users
                if obs_user
            ]
            # Filter out duplicates
            existing_ids = {ud.get("id") for ud in user_details if ud.get("id")}
            user_details.extend(
                [od for od in observer_details if od and od.get("id") not in existing_ids]
            )

        return user_details

    def _format_single_user_detail(self, user, role_type: str) -> Optional[Dict[str, Any]]:
        """Format a single user detail."""
        if not user:
            return None

        # Get uuid - try uuid first, then id
        user_uuid = None
        if hasattr(user, "uuid") and user.uuid:
            user_uuid = str(user.uuid)
        elif hasattr(user, "id") and user.id:
            user_uuid = str(user.id)

        user_serializer = UserDetailSerializer()
        # add only role_type in user data
        user.role_type = role_type
        return user_serializer.dump(user)

    async def _format_product_details(
        self, request: Requests, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Format product details from request_products relationship.
        Includes all product fields and builds category path from categories table.
        """
        if not hasattr(request, "request_products") or not request.request_products:
            return []

        product_serializer = ProductDetailSerializer()
        products = [rp.product for rp in request.request_products if rp.product]

        # Build category paths for each product
        product_data_list = []
        for product in products:
            if not product:
                continue

            # Build category path from categories table
            # Order: Parent_Cat > Sub Cat > Child Cat
            category_path_parts = []
            category_ids = []

            # Collect category IDs in correct order: parent > sub > child
            if product.parent_category_id:
                category_ids.append(product.parent_category_id)
            if product.sub_category_id:
                category_ids.append(product.sub_category_id)
            if product.category_id:
                category_ids.append(product.category_id)

            # Fetch categories
            if category_ids:
                categories_stmt = select(Categories).filter(Categories.id.in_(category_ids))
                categories_result = await db.execute(categories_stmt)
                categories = {cat.id: cat for cat in categories_result.scalars().all()}

                # Build path in order: Parent_Cat > Sub Cat > Child Cat
                for cat_id in category_ids:
                    if cat_id in categories:
                        category_path_parts.append(
                            categories[cat_id].name or categories[cat_id].code or str(cat_id)
                        )

            category_path = " > ".join(category_path_parts) if category_path_parts else None

            # Create product data dict with all fields
            product_data = {
                "id": str(product.id) if product.id else None,
                "name": product.name,
                "description": product.description,
                "quantity": product.quantity,
                "package_size": product.package_material,  # package_size maps to package_material
                "currency_id": product.currency_id,
                "target_price": float(product.price) if product.price else None,
                "certificate": [],  # Certificates not directly on product
                "status": "active" if product.active else "inactive",
                "created_at": product.created_at,
                "updated_at": product.updated_at,
            }
            product_data_list.append(product_data)
            # Store category path separately for building product_category_str
            if category_path:
                if not hasattr(request, "_product_category_paths"):
                    request._product_category_paths = []
                request._product_category_paths.append(category_path)

        return product_serializer.dump(product_data_list, many=True)

    def _format_mail_communications(self, request: Requests) -> List[Dict[str, Any]]:
        """
        Format mail communications from loaded emails.
        No loops used - uses list comprehensions.
        """
        emails = getattr(request, "_emails", [])
        if not emails:
            return []

        mail_serializer = MailCommunicationSerializer()

        return mail_serializer.dump(emails, many=True)

    def _format_document_details(self, request: Requests) -> List[Dict[str, Any]]:
        """
        Format document details from loaded documents.
        No loops used - uses list comprehensions.
        """
        documents = getattr(request, "_documents", [])
        if not documents:
            return []

        doc_serializer = DocumentDetailSerializer()

        return doc_serializer.dump(documents, many=True)

    async def _format_stage_timeline(
        self, request: Requests, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Format stage timeline with all stages for the request's phase.
        Marks stages as completed, active, or pending based on current progress.
        """
        # Get request phase
        phase_value = (
            str(request.phase.value)
            if hasattr(request.phase, "value")
            else str(request.phase) if request.phase else "deal"
        )

        logger.info(f"STEP 8.1: Fetching all stages for phase: {phase_value}")

        # Fetch all stages for this phase
        stage_method = StageMethod()
        all_stages = await stage_method.get_all_stages(db=db, phase=phase_value)

        if not all_stages:
            logger.info("STEP 8.2: No stages found for phase")
            return []

        # Get stage activities
        stage_activities = getattr(request, "request_stage_activities", [])
        
        # Find the active stage - first check current_stage on request
        active_stage_id = None
        active_stage_sequence = None
        
        if hasattr(request, "current_stage") and request.current_stage:
            active_stage_id = request.current_stage.id
            active_stage_sequence = request.current_stage.order_sequence or 0
            logger.info(f"STEP 8.2: Found active stage from current_stage: {active_stage_id}")
        else:
            # Fallback: find active stage from activities
            # Look for activities with status "active" or not completed
            for activity in stage_activities:
                if not activity.stage_id:
                    continue
                    
                activity_status = (
                    activity.status.value
                    if hasattr(activity.status, "value")
                    else str(activity.status) if activity.status else None
                )
                
                # Check if this activity is active (not completed and status is active)
                is_active = (
                    not getattr(activity, "is_completed", True)
                    or activity_status == "active"
                )
                
                if is_active:
                    active_stage_id = activity.stage_id
                    active_stage_sequence = activity.order_sequence or 0
                    logger.info(f"STEP 8.2: Found active stage from activity: {active_stage_id}")
                    break

        logger.info(
            f"STEP 8.3: Active stage ID: {active_stage_id}, Sequence: {active_stage_sequence}"
        )

        # Build stage timeline with proper statuses
        stage_timeline_data = []
        stage_serializer = StageTimelineSerializer()

        # Create a map of stage_id to activity for quick lookup (get latest activity per stage)
        stage_activity_map = {}
        for activity in stage_activities:
            if activity.stage_id:
                existing_activity = stage_activity_map.get(activity.stage_id)
                if not existing_activity:
                    stage_activity_map[activity.stage_id] = activity
                else:
                    # Compare dates to keep the latest activity
                    activity_date = activity.updated_at or activity.created_at
                    existing_date = existing_activity.updated_at or existing_activity.created_at
                    if activity_date and existing_date and activity_date > existing_date:
                        stage_activity_map[activity.stage_id] = activity
                    elif activity_date and not existing_date:
                        stage_activity_map[activity.stage_id] = activity

        for stage in all_stages:
            stage_id = stage.id
            stage_sequence = stage.order_sequence or 0
            
            # Get activity data if exists
            activity = stage_activity_map.get(stage_id)
            
            # Determine stage status based on active stage sequence and activity completion
            if active_stage_sequence is not None:
                if stage_sequence < active_stage_sequence:
                    # Stages before active stage are completed
                    stage_status = "completed"
                elif stage_sequence == active_stage_sequence:
                    # Current active stage
                    stage_status = "active"
                else:
                    # Stages after active stage are pending
                    stage_status = "pending"
            else:
                # If no active stage found, check if stage has completed activity
                if activity and getattr(activity, "is_completed", False):
                    stage_status = "completed"
                else:
                    # Mark all as pending if no active stage
                    stage_status = "pending"
            
            stage_data = {
                "id": str(stage_id) if stage_id else None,
                "stage_name": stage.stage_name or None,
                "stage_description": stage.stage_name or None,
                "stage_number": stage_sequence,
                "stage_status": stage_status,
                "created_at": activity.created_at if activity else stage.created_at,
                "updated_at": activity.updated_at if activity else stage.updated_at,
            }
            stage_timeline_data.append(stage_data)

        logger.info(f"STEP 8.4: Built timeline with {len(stage_timeline_data)} stages")

        return stage_serializer.dump(stage_timeline_data, many=True)

    def _format_request_detail_data(
        self,
        request: Requests,
        user_details: List[Dict[str, Any]],
        product_details: List[Dict[str, Any]],
        mail_communications: List[Dict[str, Any]],
        document_details: List[Dict[str, Any]],
        stage_timeline: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Format complete request detail data for API response.
        """
        phase_value = (
            str(request.phase.value)
            if hasattr(request.phase, "value")
            else str(request.phase) if request.phase else "lead"
        )
        status_value = (
            str(request.request_status.value)
            if hasattr(request.request_status, "value")
            else str(request.request_status) if request.request_status else "active"
        )

        company_name = None
        if request.company and hasattr(request.company, "company_name"):
            company_name = request.company.company_name

        # Get customer data from request_customers relationship
        customer_name = None
        customer_email = None
        customer_country = None
        customer_full_name = None
        if hasattr(request, "request_customers") and request.request_customers:
            # Get first customer (assuming one primary customer per request)
            customer_mapping = request.request_customers[0]
            if customer_mapping and customer_mapping.customer:
                customer = customer_mapping.customer
                customer_name = customer.company_name if hasattr(customer, "company_name") else None
                customer_email = (
                    customer.email_ids[0]
                    if hasattr(customer, "email_ids")
                    and isinstance(customer.email_ids, list)
                    and customer.email_ids
                    else None
                )
                customer_country = customer.country if hasattr(customer, "country") else None
                customer_full_name = customer.full_name if hasattr(customer, "full_name") else None

        # Build product category from products' categories
        product_category_str = None
        if hasattr(request, "_product_category_paths") and request._product_category_paths:
            # Use first product's category path
            product_category_str = (
                request._product_category_paths[0] if request._product_category_paths else None
            )
        # Fallback to request.product_category if available
        if (
            not product_category_str
            and request.product_category
            and isinstance(request.product_category, list)
        ):
            product_category_str = " > ".join(str(cat) for cat in request.product_category if cat)

        # Format request_id
        request_id = (
            request.deal_id
            or (
                " - ".join(
                    filter(
                        None,
                        [
                            request.lead,
                            customer_name or request.name,
                            product_category_str,
                        ],
                    )
                )
            )
            or str(request.id)
        )

        # Build request detail data dictionary
        request_detail_data = {
            "id": str(request.id),
            "name": request.name or None,
            "phase": phase_value,
            "request_id": request_id,
            "customer_company_name": customer_name,
            "customer_email": customer_email,
            "customer_country": customer_country,
            "customer_full_name": customer_full_name,
            "priority": request.priority or None,
            "bitrix_url": request.bitrix_url or None,
            "bitrix_id": request.bitrix_id,
            "company_name": company_name or None,
            "group_name": company_name or None,
            "prodcut_category": product_category_str,
            "status": status_value,
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "user_details": user_details or [],
            "product_details": product_details or [],
            "mail_communication": mail_communications or [],
            "document_details": document_details or [],
            "stage_timeline": stage_timeline or [],
            "last_contact": request.last_contact,
            "etd": request.etd,
            "destination_country": request.destination_country,
        }

        return request_detail_data
