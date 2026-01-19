"""
Get supplier detail service for retrieving complete supplier information.
Refactored to use join queries and serializers.
"""

import logging
from typing import Any, Dict, List

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.v1.api.suppliers.models.methods import SupplierMethod, DocumentRepository
from apps.v1.api.suppliers.models.model import Suppliers, SupplierEmail
from apps.v1.api.suppliers.serializer import SupplierDetailResponseSerializer

from apps.v1.api.products.models.model import Categories
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class GetSupplierDetailService:
    """
    Service to get complete supplier details with nested product, price history, mail communication, and document information.
    Uses join queries and serializers for efficient data retrieval.
    """

    def __init__(self):
        self.supplier_method = SupplierMethod(Suppliers)

    def _get_valid_category_name(self, category: Categories) -> str:
        """
        Extract a valid category name from a Categories object.
        Filters out invalid values like "false", "null", empty strings, or JSON arrays.

        Args:
            category: Categories model instance

        Returns:
            Valid category name string or empty string if invalid
        """
        if not category:
            return ""

        # Try name first
        if hasattr(category, "name") and category.name:
            name_val = str(category.name).strip()
            # Filter out invalid values
            if (
                name_val
                and name_val.lower() not in ("false", "null", "none", "")
                and not name_val.startswith("[")
            ):
                return name_val

        # Fallback to code
        if hasattr(category, "code") and category.code:
            code_val = str(category.code).strip()
            # Filter out invalid values
            if (
                code_val
                and code_val.lower() not in ("false", "null", "none", "")
                and not code_val.startswith("[")
            ):
                return code_val

        return ""

    async def get_supplier_detail(
        self,
        db: AsyncSession,
        supplier_id: str,
    ):
        """
        Get complete supplier details by ID.

        Args:
            db: Database session
            supplier_id: Supplier ID (integer as string)

        Returns:
            StandardResponse with complete supplier details
        """
        try:
            logger.info("Starting supplier detail retrieval workflow")

            # Validate supplier_id
            try:
                db_id = int(supplier_id)
            except ValueError:
                logger.error(f"Invalid supplier ID format: {supplier_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Supplier ID must be a valid integer",
                ).make

            # Get supplier with relationships using method
            supplier = await self.supplier_method.find_by_id(db=db, supplier_id=db_id)

            if not supplier:
                logger.error(f"Supplier not found: {supplier_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message="Supplier not found",
                ).make

            logger.info(f"Supplier found: {supplier.id}")

            # Format product details from loaded relationships
            product_details = await self._format_product_details(supplier, db)

            # Format price history details from products
            price_history_details = await self._format_price_history_details(supplier, db)

            # Format mail communications
            mail_communications = await self._format_mail_communications(supplier, db)

            # Format document details
            document_details = await self._format_document_details(supplier, db)

            # Format supplier data
            supplier_data = await self._format_supplier_data(
                supplier,
                product_details,
                price_history_details,
                mail_communications,
                document_details,
                db,
            )

            # Build response
            response_data = {
                "status": constant_variable.STATUS_SUCCESS,
                "data": supplier_data,
                "message": message_variable.SUPPLIER_RETRIEVED_SUCCESS,
            }

            # Serialize complete response
            response_serializer = SupplierDetailResponseSerializer()
            serialized_response = response_serializer.dump(response_data)

            logger.info("Supplier detail retrieval successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_response.get("data"),
                message=serialized_response.get(
                    "message", message_variable.SUPPLIER_RETRIEVED_SUCCESS
                ),
            ).make

        except ValueError as exc:
            logger.error(
                f"Validation error in get_supplier_detail_service: {exc}",
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
                f"Database error in get_supplier_detail_service: {exc}",
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
                f"Unexpected error in get_supplier_detail_service: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    async def _format_product_details(
        self, supplier: Suppliers, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Format product details from supplier's product_suppliers relationship.
        Uses categories table to build category paths.
        """
        if not hasattr(supplier, "product_suppliers") or not supplier.product_suppliers:
            return []

        # Collect all category IDs from products
        all_category_ids = set()
        products = []

        for ps_mapping in supplier.product_suppliers:
            product = getattr(ps_mapping, "product", None) if ps_mapping else None
            if product:
                products.append(product)
                if hasattr(product, "parent_category_id") and product.parent_category_id:
                    all_category_ids.add(product.parent_category_id)
                if hasattr(product, "sub_category_id") and product.sub_category_id:
                    all_category_ids.add(product.sub_category_id)
                if hasattr(product, "category_id") and product.category_id:
                    all_category_ids.add(product.category_id)

        # Fetch all categories in one query
        categories_map = await self.supplier_method.get_categories_map(
            db=db, category_ids=list(all_category_ids)
        )

        # Format product details
        product_details = []
        for product in products:
            # Build category path from categories table
            category_name = ""
            sub_category_name = ""
            child_category_name = ""

            category_ids_ordered = []
            if hasattr(product, "parent_category_id") and product.parent_category_id:
                category_ids_ordered.append(product.parent_category_id)
            if hasattr(product, "sub_category_id") and product.sub_category_id:
                category_ids_ordered.append(product.sub_category_id)
            if hasattr(product, "category_id") and product.category_id:
                category_ids_ordered.append(product.category_id)

            if category_ids_ordered and categories_map:
                category_path_parts = []
                for cat_id in category_ids_ordered:
                    if cat_id in categories_map:
                        category = categories_map[cat_id]
                        category_name_value = self._get_valid_category_name(category)
                        if category_name_value:
                            category_path_parts.append(category_name_value)

                if len(category_path_parts) >= 1:
                    category_name = category_path_parts[0]
                if len(category_path_parts) >= 2:
                    sub_category_name = category_path_parts[1]
                if len(category_path_parts) >= 3:
                    child_category_name = category_path_parts[2]

            # Fallback to product.product_category
            if (
                not category_name
                and hasattr(product, "product_category")
                and product.product_category
            ):
                cat_val = str(product.product_category).strip()
                # Filter out invalid values
                if (
                    cat_val
                    and cat_val.lower() not in ("false", "null", "none", "")
                    and not cat_val.startswith("[")
                ):
                    category_name = cat_val

            # Get MOQ (prefer production, fallback to packaging material)
            moq = None
            if hasattr(product, "moq_production") and product.moq_production:
                moq = product.moq_production
            elif hasattr(product, "moq_packaging_matereal") and product.moq_packaging_matereal:
                moq = product.moq_packaging_matereal

            # Get lead_time (from lead_time_to_production)
            lead_time = None
            if hasattr(product, "lead_time_to_production") and product.lead_time_to_production:
                lead_time = product.lead_time_to_production

            product_data = {
                "id": str(product.id) if product.id else None,
                "name": product.name or "",
                "sku_id": product.code if hasattr(product, "code") and product.code else None,
                "description": product.description or "",
                "category": "",  # Empty string as per API spec
                "sub_category": "",  # Empty string as per API spec
                "child_category": "",  # Empty string as per API spec
                "image_url": (
                    product.preview_picture or product.detail_picture or ""
                    if hasattr(product, "preview_picture") or hasattr(product, "detail_picture")
                    else ""
                ),
                "price": (
                    float(product.price)
                    if hasattr(product, "price") and product.price is not None
                    else 0.0
                ),
                "currency": product.currency_id or None,
                "moq": moq,
                "lead_time": lead_time,
                "primary_supplier_name": supplier.company_name or supplier.supplier_name or "",
                "created_at": product.created_at if hasattr(product, "created_at") else None,
                "updated_at": product.updated_at if hasattr(product, "updated_at") else None,
                "status": (
                    "active" if (hasattr(product, "active") and product.active) else "inactive"
                ),
            }
            product_details.append(product_data)

        return product_details

    async def _format_price_history_details(
        self, supplier: Suppliers, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Format price history details from supplier's products.
        Creates price history entries from product prices.
        """
        if not hasattr(supplier, "product_suppliers") or not supplier.product_suppliers:
            return []

        price_history = []
        for ps_mapping in supplier.product_suppliers:
            product = getattr(ps_mapping, "product", None) if ps_mapping else None
            if product and hasattr(product, "price") and product.price is not None:
                price_history.append(
                    {
                        "id": str(product.id) if product.id else None,
                        "product_name": product.name or "",
                        "price": float(product.price),
                        "currency": product.currency_id or None,
                        "effective_from": (
                            product.created_at if hasattr(product, "created_at") else None
                        ),
                        "effective_to": (
                            product.updated_at if hasattr(product, "updated_at") else None
                        ),
                    }
                )

        # Serialize price history
        return price_history

    async def _format_mail_communications(
        self, supplier: Suppliers, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Format mail communications from emails table.
        Fetches emails where mapping_id = supplier.id and mapping_table = 'supplier'.
        """
        try:
            emails_stmt = (
                select(SupplierEmail)
                .options(selectinload(SupplierEmail.emails))
                .where(SupplierEmail.supplier_id == supplier.id)
            )
            emails_result = await db.execute(emails_stmt)
            emails = emails_result.scalars().all()

            if not emails:
                return []

            # Format email data
            mail_communications = []
            for email in emails:
                email_conversation = email.emails

                mail_data = {
                    "id": str(email_conversation.id) if email_conversation.id else None,
                    "to_person_name": email_conversation.receiver_string or "",
                    "to_person_email": email_conversation.receiver_json or "",
                    "from_person_email": email_conversation.sender_email or "",
                    "subject": email_conversation.subject or "",
                    "content": email_conversation.content_text or "",
                    "mail_type": "received" if email_conversation.received_at else "sent",
                    "status": "active",
                    "created_at": email_conversation.created_at,
                    "updated_at": email_conversation.updated_at,
                    "sent_at": email_conversation.sent_at,
                    "received_at": email_conversation.received_at,
                }
                mail_communications.append(mail_data)

            return mail_communications

        except Exception as e:
            logger.error(f"Error formatting mail communications: {e}", exc_info=True)
            return []

    async def _format_document_details(
        self, supplier: Suppliers, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Format document details from documents table.
        Fetches documents where mapping_id = supplier.id and source_table = 'suppliers'.
        """
        try:
            documents = await DocumentRepository.get_documents_by_source(
                db=db, source_table="suppliers", mapping_id=supplier.id
            )

            if not documents:
                return []

            return documents

        except Exception as e:
            logger.error(f"Error formatting document details: {e}", exc_info=True)
            return []

    async def _format_supplier_data(
        self,
        supplier: Suppliers,
        product_details: List[Dict[str, Any]],
        price_history_details: List[Dict[str, Any]],
        mail_communications: List[Dict[str, Any]],
        document_details: List[Dict[str, Any]],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Format supplier data for response.
        """
        # Build address
        address_parts = [
            supplier.street_address or "",
            supplier.city or "",
            supplier.zip or "",
            supplier.state or "",
        ]
        address = ", ".join(filter(None, address_parts))

        # Parse messenger data
        messanger_type = ""
        messanger_number = ""
        if supplier.messenger:
            try:
                import json

                messenger_data = (
                    json.loads(supplier.messenger)
                    if isinstance(supplier.messenger, str)
                    else supplier.messenger
                )
                if isinstance(messenger_data, list) and len(messenger_data) > 0:
                    first_messenger = messenger_data[0]
                    if isinstance(first_messenger, dict):
                        messanger_type = first_messenger.get("VALUE_TYPE", "")
                        messanger_number = first_messenger.get("VALUE", "")
            except (json.JSONDecodeError, TypeError, AttributeError):
                messanger_number = str(supplier.messenger) if supplier.messenger else ""

        # Format email (handle JSON array)
        email_str = ""
        if supplier.email:
            if isinstance(supplier.email, list) and len(supplier.email) > 0:
                email_value = (
                    supplier.email[0].get("VALUE")
                    if isinstance(supplier.email[0], dict)
                    else supplier.email[0]
                )
                email_str = email_value or ""
            elif isinstance(supplier.email, str):
                email_str = supplier.email

        # Format phone (handle JSON array)
        phone_str = ""
        if supplier.phone:
            if isinstance(supplier.phone, list) and len(supplier.phone) > 0:
                phone_value = (
                    supplier.phone[0].get("VALUE")
                    if isinstance(supplier.phone[0], dict)
                    else supplier.phone[0]
                )
                phone_str = phone_value or ""
            elif isinstance(supplier.phone, str):
                phone_str = supplier.phone

        # Format website (handle JSON array)
        website_str = ""
        if supplier.website:
            if isinstance(supplier.website, list) and len(supplier.website) > 0:
                website_value = (
                    supplier.website[0].get("VALUE")
                    if isinstance(supplier.website[0], dict)
                    else supplier.website[0]
                )
                website_str = website_value or ""
            elif isinstance(supplier.website, str):
                website_str = supplier.website

        # Build category arrays from all products
        category_list = []
        sub_category_list = []
        child_category_list = []

        if hasattr(supplier, "product_suppliers") and supplier.product_suppliers:
            for ps_mapping in supplier.product_suppliers:
                product = getattr(ps_mapping, "product", None) if ps_mapping else None
                if product:
                    # Collect category IDs
                    if hasattr(product, "parent_category_id") and product.parent_category_id:
                        category_list.append(product.parent_category_id)
                    if hasattr(product, "sub_category_id") and product.sub_category_id:
                        sub_category_list.append(product.sub_category_id)
                    if hasattr(product, "category_id") and product.category_id:
                        child_category_list.append(product.category_id)

        # Fetch categories and build category name arrays
        all_category_ids = set(category_list + sub_category_list + child_category_list)
        categories_map = {}
        if all_category_ids:
            categories_query = select(Categories).filter(Categories.id.in_(list(all_category_ids)))
            categories_result = await db.execute(categories_query)
            categories_map = {cat.id: cat for cat in categories_result.scalars().all()}

        # Build category name arrays
        category_names = []
        for cat_id in set(category_list):
            if cat_id in categories_map:
                cat_name = self._get_valid_category_name(categories_map[cat_id])
                if cat_name and cat_name not in category_names:
                    category_names.append(cat_name)

        sub_category_names = []
        for cat_id in set(sub_category_list):
            if cat_id in categories_map:
                cat_name = self._get_valid_category_name(categories_map[cat_id])
                if cat_name and cat_name not in sub_category_names:
                    sub_category_names.append(cat_name)

        child_category_names = []
        for cat_id in set(child_category_list):
            if cat_id in categories_map:
                cat_name = self._get_valid_category_name(categories_map[cat_id])
                if cat_name and cat_name not in child_category_names:
                    child_category_names.append(cat_name)

        # Fallback to supplier.product_category if no categories found
        if not category_names and supplier.product_category:
            if isinstance(supplier.product_category, str):
                # Filter out invalid values
                cat_val = str(supplier.product_category).strip()
                if (
                    cat_val
                    and cat_val.lower() not in ("false", "null", "none", "")
                    and not cat_val.startswith("[")
                ):
                    category_names = [cat_val]
            elif isinstance(supplier.product_category, list):
                # Filter out invalid values from list
                category_names = [
                    str(cat).strip()
                    for cat in supplier.product_category
                    if cat
                    and str(cat).strip()
                    and str(cat).strip().lower() not in ("false", "null", "none", "")
                    and not str(cat).strip().startswith("[")
                ]

        return {
            "id": str(supplier.id),
            "company_name": supplier.company_name or "",
            "email": email_str or None,
            "phone_number": phone_str or None,
            "created_by": supplier.created_by or "",
            "website": website_str or None,
            "messanger_type": messanger_type,
            "messanger_number": messanger_number or None,
            "rating": float(supplier.stars) if supplier.stars is not None else 0.0,
            "address": address,
            "country": supplier.country or "",
            "responsible_person_name": supplier.responsible_person or None,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at,
            "updated_by": supplier.modified_by or "",
            "created_on": supplier.created_on or None,
            "last_contact": supplier.last_contact or None,
            "prefix": supplier.prefix or None,
            "company_type": supplier.company_type or None,
            "industry": supplier.industry or None,
            "vat_number": supplier.rq_vat_id or None,
            "registraction_number": supplier.registration_number or None,
            "supplier_name": supplier.supplier_name or None,
            "type_of_buyer": supplier.type_of_buyer or None,
            "category": category_names,
            "sub_category": sub_category_names,
            "child_category": child_category_names,
            "products_manufactured": supplier.products_manufactured or "",
            "product_details": product_details or [],
            "price_history_details": price_history_details or [],
            "mail_communication": mail_communications or [],
            "document_details": document_details or [],
            "assigned_by": supplier.assigned_by_user.name if supplier.assigned_by_user else None,
            "generated_by": supplier.generated_by_user.name if supplier.generated_by_user else None,
            "updated_by": supplier.updated_by_user.name if supplier.updated_by_user else None,
        }
