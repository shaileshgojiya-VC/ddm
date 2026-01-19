"""
Helper methods for transforming request model data into serializer format.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from apps.v1.api.request.models.model import Requests, Stage
from apps.v1.api.auth.models.model import Users
from apps.v1.api.products.models.model import Products

logger = logging.getLogger(__name__)


class RequestHelperMethod:
    """Helper methods for transforming request model data into API response format."""

    @staticmethod
    def format_enum_value(enum_value: Any) -> Optional[str]:
        """
        Format enum value to string.

        Args:
            enum_value: Enum value to format

        Returns:
            String representation of enum or None
        """
        if enum_value is None:
            return None
        if isinstance(enum_value, Enum):
            return enum_value.value
        return str(enum_value)

    @staticmethod
    def format_product_category(product_category: Optional[List]) -> Optional[str]:
        """
        Format product category list to string format.

        Args:
            product_category: List of category strings

        Returns:
            Formatted string like "dairy > uht-milk > uht-milk-1" or None
        """
        if not product_category or not isinstance(product_category, list):
            return None
        return " > ".join(str(cat) for cat in product_category if cat)

    @staticmethod
    def format_request_id(request: Requests) -> str:
        """
        Format request_id from request data.

        Args:
            request: Requests model instance

        Returns:
            Formatted request_id string
        """
        if request.deal_id:
            return request.deal_id

        parts = []
        if request.lead:
            parts.append(request.lead)
        if request.company and hasattr(request.company, "company_name"):
            parts.append(request.company.company_name)
        elif request.name:
            parts.append(request.name)

        if request.product_category:
            category_str = RequestHelperMethod.format_product_category(
                request.product_category
            )
            if category_str:
                parts.append(category_str)

        return " - ".join(parts) if parts else str(request.id)

    @staticmethod
    def format_user_detail(
        user: Optional[Users], role_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Format user data for user_details array.

        Args:
            user: Users model instance
            role_type: Role type (observer, approver, responsible)

        Returns:
            Formatted user detail dictionary or None
        """
        if not user:
            return None

        return {
            "uuid": str(user.uuid) if user.uuid else None,
            "name": user.name if user.name else None,
            "email": user.email if user.email else None,
            "role": user.role.name
            if user.role and hasattr(user.role, "name")
            else None,
            "role_type": role_type,
        }

    @staticmethod
    def format_user_details(
        request: Requests,
        responsible_user: Optional[Users] = None,
        created_user: Optional[Users] = None,
        modified_user: Optional[Users] = None,
    ) -> List[Dict[str, Any]]:
        """
        Format user details array from request and related users.

        Args:
            request: Requests model instance
            responsible_user: User who is responsible for the request
            created_user: User who created the request
            modified_user: User who last modified the request

        Returns:
            List of formatted user detail dictionaries
        """
        user_details = []

        if responsible_user:
            user_detail = RequestHelperMethod.format_user_detail(
                responsible_user, "responsible"
            )
            if user_detail:
                user_details.append(user_detail)

        if created_user and created_user.uuid != (
            responsible_user.uuid if responsible_user else None
        ):
            user_detail = RequestHelperMethod.format_user_detail(
                created_user, "observer"
            )
            if user_detail:
                user_details.append(user_detail)

        if modified_user and modified_user.uuid not in [
            (responsible_user.uuid if responsible_user else None),
            (created_user.uuid if created_user else None),
        ]:
            user_detail = RequestHelperMethod.format_user_detail(
                modified_user, "observer"
            )
            if user_detail:
                user_details.append(user_detail)

        return user_details

    @staticmethod
    def format_product_detail(product: Optional[Products]) -> Optional[Dict[str, Any]]:
        """
        Format product data for product_details array.

        Args:
            product: Products model instance

        Returns:
            Formatted product detail dictionary or None
        """
        if not product:
            return None

        return {
            "uuid": str(product.uuid) if product.uuid else None,
            "name": product.name if product.name else None,
            "description": getattr(product, "description", None),
            "quantity": getattr(product, "quantity", None),
            "package_size": getattr(product, "package_size", None),
            "target_price": float(product.price)
            if hasattr(product, "price") and product.price
            else None,
            "certificate": getattr(product, "certificate", []) or [],
            "status": "active"
            if (hasattr(product, "active") and product.active)
            else "inactive",
            "created_at": product.created_at
            if hasattr(product, "created_at")
            else None,
            "updated_at": product.updated_at
            if hasattr(product, "updated_at")
            else None,
        }

    @staticmethod
    def format_product_details(
        products: Optional[List[Products]],
    ) -> List[Dict[str, Any]]:
        """
        Format product details array from products list.

        Args:
            products: List of Products model instances

        Returns:
            List of formatted product detail dictionaries
        """
        if not products:
            return []

        return [
            detail
            for product in products
            if (detail := RequestHelperMethod.format_product_detail(product))
            is not None
        ]

    @staticmethod
    def format_mail_communication_item(
        uuid: Optional[str] = None,
        to_person_name: Optional[str] = None,
        to_person_email: Optional[str] = None,
        from_person_email: Optional[str] = None,
        subject: Optional[str] = None,
        content: Optional[str] = None,
        mail_type: Optional[str] = None,
        attachments: Optional[List] = None,
        status: Optional[str] = None,
        created_at: Optional[Any] = None,
        updated_at: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Format mail communication item for mail_communication array.

        Args:
            uuid: Mail communication UUID
            to_person_name: Recipient name
            to_person_email: Recipient email
            from_person_email: Sender email
            subject: Email subject
            content: Email content (HTML)
            mail_type: Type of mail (received, sent)
            attachments: List of attachments
            status: Status of mail communication
            created_at: Creation timestamp
            updated_at: Update timestamp

        Returns:
            Formatted mail communication dictionary
        """
        return {
            "uuid": str(uuid) if uuid else None,
            "to_person_name": to_person_name,
            "to_person_email": to_person_email,
            "from_person_email": from_person_email,
            "subject": subject,
            "content": content,
            "mail_type": mail_type,
            "attachments": attachments or [],
            "status": status or "active",
            "created_at": created_at,
            "updated_at": updated_at,
        }

    @staticmethod
    def format_mail_communications(
        mail_items: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Format mail communications array.

        Args:
            mail_items: List of mail communication dictionaries

        Returns:
            List of formatted mail communication dictionaries
        """
        if not mail_items:
            return []

        return [
            RequestHelperMethod.format_mail_communication_item(**item)
            for item in mail_items
        ]

    @staticmethod
    def format_document_detail(
        uuid: Optional[str] = None,
        name: Optional[str] = None,
        url: Optional[str] = None,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        status: Optional[str] = None,
        created_at: Optional[Any] = None,
        updated_at: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Format document data for document_details array.

        Args:
            uuid: Document UUID
            name: Document name
            url: Document URL
            file_name: File name
            file_type: File type
            file_size: File size in bytes
            status: Document status
            created_at: Creation timestamp
            updated_at: Update timestamp

        Returns:
            Formatted document detail dictionary
        """
        return {
            "uuid": str(uuid) if uuid else None,
            "name": name,
            "url": url,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "status": status or "active",
            "created_at": created_at,
            "updated_at": updated_at,
        }

    @staticmethod
    def format_document_details(
        documents: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Format document details array.

        Args:
            documents: List of document dictionaries

        Returns:
            List of formatted document detail dictionaries
        """
        if not documents:
            return []

        return [RequestHelperMethod.format_document_detail(**doc) for doc in documents]

    @staticmethod
    def format_stage_timeline_item(stage: Optional[Stage]) -> Optional[Dict[str, Any]]:
        """
        Format stage data for stage_timeline array.

        Args:
            stage: Stage model instance

        Returns:
            Formatted stage timeline dictionary or None
        """
        if not stage:
            return None

        stage_status_value = RequestHelperMethod.format_enum_value(stage.stage_status)

        stage_status_mapping = {
            "new_unclear": "pending_response",
            "new_clear": "on_track",
            "continue": "on_track",
            "reject": "delayed",
            "accept": "awaiting_client",
            "approved": "followed_up_required",
        }

        mapped_status = stage_status_mapping.get(stage_status_value, stage_status_value)

        return {
            "uuid": str(stage.uuid) if stage.uuid else None,
            "stage_name": stage.stage_name if stage.stage_name else None,
            "stage_description": getattr(stage, "stage_description", None)
            or stage.stage_name
            or None,
            "stage_number": stage.order_sequence
            if hasattr(stage, "order_sequence")
            else None,
            "stage_status": mapped_status,
            "created_at": stage.created_at if hasattr(stage, "created_at") else None,
            "updated_at": stage.updated_at if hasattr(stage, "updated_at") else None,
        }

    @staticmethod
    def format_stage_timeline(stages: Optional[List[Stage]]) -> List[Dict[str, Any]]:
        """
        Format stage timeline array from stages list.

        Args:
            stages: List of Stage model instances

        Returns:
            List of formatted stage timeline dictionaries, sorted by order_sequence
        """
        if not stages:
            return []

        timeline = [
            item
            for stage in stages
            if (item := RequestHelperMethod.format_stage_timeline_item(stage))
            is not None
        ]

        timeline.sort(key=lambda x: x.get("stage_number", 0) or 0)

        return timeline

    @staticmethod
    def format_request_detail_data(
        request: Requests,
        user_details: Optional[List[Dict[str, Any]]] = None,
        product_details: Optional[List[Dict[str, Any]]] = None,
        mail_communications: Optional[List[Dict[str, Any]]] = None,
        document_details: Optional[List[Dict[str, Any]]] = None,
        stage_timeline: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Format complete request detail data for API response.

        Args:
            request: Requests model instance
            user_details: List of user detail dictionaries
            product_details: List of product detail dictionaries
            mail_communications: List of mail communication dictionaries
            document_details: List of document detail dictionaries
            stage_timeline: List of stage timeline dictionaries

        Returns:
            Complete formatted request detail dictionary
        """
        phase_value = RequestHelperMethod.format_enum_value(request.phase)
        status_value = RequestHelperMethod.format_enum_value(request.request_status)

        company_name = None
        if request.company and hasattr(request.company, "company_name"):
            company_name = request.company.company_name

        return {
            "uuid": str(request.id) if request.id else None,
            "name": request.name,
            "phase": phase_value or "lead",
            "request_id": RequestHelperMethod.format_request_id(request),
            "customer_name": company_name or request.name or None,
            "customer_email": request.email or None,
            "customer_country": request.country or None,
            "priority": request.urgency_level or None,
            "bitrix_url": request.bitrix_url or None,
            "bitrix_id": request.bitrix_id,
            "company_name": company_name or None,
            "group_name": getattr(request, "group_name", None) or company_name or None,
            "prodcut_category": RequestHelperMethod.format_product_category(
                request.product_category
            ),
            "status": status_value or "active",
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "user_details": user_details or [],
            "product_details": product_details or [],
            "mail_communication": mail_communications or [],
            "document_details": document_details or [],
            "stage_timeline": stage_timeline or [],
        }
