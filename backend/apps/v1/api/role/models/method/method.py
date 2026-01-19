"""
Role database methods for role-related database operations.
"""

import logging

from typing import Dict, List

from sqlalchemy import select, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.auth.models.model import Modules, Roles
from apps.v1.api.auth.models.attribute import Status

logger = logging.getLogger(__name__)


class RoleAuthMethod:
    """
    Role database methods for role-related database queries.
    
    Args:
        model: Role model class

    Returns:
        RoleAuthMethod instance with database query methods
    """
    
    def __init__(self, model):
        self.model = model

    async def list_roles(
        self,
        db: AsyncSession,
        search: str = None,
        page: int = 1,
        limit: int = 10,
    ):
        """
        List roles with search and pagination.
        
        Args:
            db: Database session
            search: Search query (searches name and description)
            page: Page number
            limit: Page limit

        Returns:
            Tuple of (list of roles, total count)
        """
        try:
            logger.info("Starting list roles query")

            # Build base query
            stmt = select(self.model)

            # Exclude deleted roles
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
            roles = result.scalars().all()

            logger.info(f"Found {len(roles)} roles (total: {total})")

            return roles, total

        except SQLAlchemyError as exc:
            logger.error(f"Database error in list_roles: {exc}", exc_info=True)
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in list_roles: {exc}", exc_info=True)
            raise

    async def get_modules_map(self, db: AsyncSession) -> Dict[str, str]:
        """
        Fetch modules needed for role access and return a name->slug map (lowercased keys).
        
        Args:
            db: Database session
            
        Returns:
            Dictionary mapping module names (lowercase) to their slugs
        """
        required_names = {
            "dashboard",
            "user management",
            "users",
            "settings",
            "inquiry management",
            "messages",
            "products",
            "supplier",
            "suppliers",
            #"deals",
            "ai assistant",
            "ai-assistant",
        }

        stmt = select(Modules).where(
            func.lower(Modules.name).in_(required_names)
        )
        result = await db.execute(stmt)
        modules = result.scalars().all()

        modules_map: Dict[str, str] = {}
        for module in modules:
            modules_map[module.name.lower()] = module.slug or module.name

        # Add aliases for common plural/slug variants
        if "supplier" in modules_map and "suppliers" not in modules_map:
            modules_map["suppliers"] = modules_map["supplier"]
        if "user management" in modules_map and "users" not in modules_map:
            modules_map["users"] = modules_map["user management"]
        if "ai assistant" in modules_map and "ai-assistant" not in modules_map:
            modules_map["ai-assistant"] = modules_map["ai assistant"]
        if "messages" in modules_map and "mesages" not in modules_map:
            modules_map["mesages"] = modules_map["messages"]
        return modules_map

    def modules_for_role(self, role_name: str, modules_map: Dict[str, str]) -> List[str]:
        """
        Resolve module slugs for a given role name using predefined access rules.
        
        Args:
            role_name: Name of the role
            modules_map: Dictionary mapping module names to slugs
            
        Returns:
            List of module slugs for the role
        """
        role_key = role_name.lower()

        role_modules = {
            "admin": ["dashboard", "users", "settings"],
            "management": [
                "dashboard",
                #"deals",
                "inquiry management",
                "users",
                "messages",
                "products",
                "suppliers",
                "ai-assistant",
            ],
            "sales": [
                "dashboard",
                #"deals",
                "inquiry management",
                "messages",
                "products",
                "suppliers",    
                "ai-assistant",
            ],
            "staff": [
                "dashboard",
                #"deals",
                "inquiry management",
                "messages",
                "products",
                "supplier",
                "ai-assistant",
            ],
        }

        names = role_modules.get(role_key, [])
        module_names: List[str] = []
        for name in names:
            module_name = modules_map.get(name.lower())
            if module_name and module_name not in module_names:
                module_names.append(module_name)
        return module_names
