"""
Module database methods for module-related database operations.
"""

import logging

from sqlalchemy import select, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.model import Modules
from apps.v1.api.auth.models.attribute import Status

logger = logging.getLogger(__name__)


class ModuleAuthMethod:
    """
    Module database methods for module-related database queries.
    
    Args:
        model: Module model class

    Returns:
        ModuleAuthMethod instance with database query methods
    """
    
    def __init__(self, model):
        self.model = model

    async def list_modules(
        self,
        db: AsyncSession,
        search: str = None,
        page: int = 1,
        limit: int = 10,
    ):
        """
        List modules with search and pagination.
        
        Args:
            db: Database session
            search: Search query (searches name, slug, and description)
            page: Page number
            limit: Page limit

        Returns:
            Tuple of (list of modules, total count)
        """
        try:
            logger.info("Starting list modules query")

            # Build base query
            stmt = select(self.model)

            # Exclude deleted modules
            stmt = stmt.filter(
                or_(
                    self.model.status != Status.DELETED,
                    self.model.deleted_at.is_(None),
                )
            )

            # Apply search filter
            if search:
                search_pattern = f"%{search}%"
                stmt = stmt.filter(
                    or_(
                        self.model.name.ilike(search_pattern),
                        self.model.slug.ilike(search_pattern),
                        self.model.description.ilike(search_pattern),
                    )
                )

            # Get total count with same filters
            count_stmt = select(func.count(self.model.id))
            count_stmt = count_stmt.filter(
                or_(
                    self.model.status != Status.DELETED,
                    self.model.deleted_at.is_(None),
                )
            )
            if search:
                search_pattern = f"%{search}%"
                count_stmt = count_stmt.filter(
                    or_(
                        self.model.name.ilike(search_pattern),
                        self.model.slug.ilike(search_pattern),
                        self.model.description.ilike(search_pattern),
                    )
                )

            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0

            # Apply pagination
            offset = (page - 1) * limit
            stmt = stmt.offset(offset).limit(limit)

            # Order by created_at descending
            stmt = stmt.order_by(self.model.created_at.desc())

            # Execute query
            result = await db.execute(stmt)
            modules = result.scalars().all()

            logger.info(f"Found {len(modules)} modules (total: {total})")

            return modules, total

        except SQLAlchemyError as exc:
            logger.error(f"Database error in list_modules: {exc}", exc_info=True)
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in list_modules: {exc}", exc_info=True)
            raise

