"""
Database utility methods for Logistic operations.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.logistic.models.model import Logistic

logger = logging.getLogger(__name__)


class LogisticRepository:
    """Repository class for Logistic database operations."""

    @staticmethod
    async def get_logistic_by_product_id(
        db: AsyncSession, product_id: int
    ) -> Optional[Logistic]:
        """
        Get logistic details for a product by product_id.

        Args:
            db: Database session
            product_id: Product ID

        Returns:
            Optional[Logistic]: Logistic record if found, None otherwise
        """
        if not product_id:
            return None

        logger.info(f"STEP: Fetching logistic for product_id: {product_id}")

        result = await db.execute(
            select(Logistic).where(Logistic.product_id == product_id).limit(1)
        )
        logistic = result.scalar_one_or_none()

        if logistic:
            logger.info(
                f"STEP: Found logistic record with id: {logistic.id} for product_id: {product_id}"
            )
        else:
            logger.info(f"STEP: No logistic record found for product_id: {product_id}")

        return logistic
