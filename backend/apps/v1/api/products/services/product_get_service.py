"""
Service for retrieving product details.
"""

import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.products.models.methods import GetProductDetailsDatabaseHelper
from apps.v1.api.products.serializer import ProductResposeSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class ProductGetService:
    """
    Service class for retrieving product details.

    Provides business logic for retrieving complete product information
    including core details, supplier details, logistics details, and documents.
    """

    async def get_product_details(
        self,
        db: AsyncSession,
        product_id: int,
    ):
        """
        Retrieve complete product details by ID.

        Args:
            db: Database session
            product_id: Product ID to retrieve

        Returns:
            StandardResponse with complete product details
        """
        try:
            logger.info("STEP 1: Starting product details retrieval workflow")
            logger.info(f"STEP 2: Validating product_id: {product_id}")

            if not product_id or product_id <= 0:
                logger.error("STEP ERROR: Invalid product_id provided")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=constant_variable.STATUS_NULL,
                    message="Invalid product ID",
                ).make

            logger.info(f"STEP 3: Fetching complete product details for ID: {product_id}")
            product_details = await GetProductDetailsDatabaseHelper.get_product_details(
                db=db, product_id=product_id
            )

            if not product_details or not product_details.get("product"):
                logger.error(f"STEP ERROR: Product not found with ID: {product_id}")
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message="Product not found",
                ).make

            product = product_details["product"]

            logger.info("STEP 4: Preparing data structure for serialization")
            supplier_list = product_details.get("supplier", [])
            logistics_obj = product_details.get("logistics")
            documents_list = product_details.get("documents", [])

            # Attach nested data to product object for serializer
            # Serializer will handle the transformation
            # IMPORTANT: Store user names in non-database attributes to avoid SQLAlchemy tracking
            # The serializer will use these via method fields
            setattr(product, "_serializer_updated_by", product_details.get("updated_by"))
            setattr(product, "_serializer_generated_by", product_details.get("generated_by"))
            setattr(product, "supplier_details", supplier_list)
            setattr(product, "logistics_details", logistics_obj)
            setattr(product, "document_details", documents_list)

            logger.info("STEP 5: Serializing product response")
            product_serializer = ProductResposeSerializer()
            serialized_data = product_serializer.dump(product)

            logger.info("STEP 6: Product details retrieval completed successfully")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_data,
                message=message_variable.PRODUCT_RETRIEVED_SUCCESS,
            ).make

        except ValueError as exc:
            logger.error(
                f"STEP ERROR: Validation error in get_product_details: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=str(exc),
            ).make

        except Exception as exc:
            logger.error(
                f"STEP ERROR: Unexpected error in get_product_details: {exc}",
                exc_info=True,
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
