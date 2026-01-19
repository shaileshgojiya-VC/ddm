"""
Model methods for authentication with both sync and async support.
"""

import logging
from datetime import datetime

from sqlalchemy import column, func, or_, select, table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from apps.v1.api.request.models.attribute import RequestPhase, RequestStatus

from apps.v1.api.auth.models.attribute import Status
from apps.v1.api.auth.models.model import Roles, Users
from apps.v1.api.request.models.model import Requests, RequestStageActivity

logger = logging.getLogger(__name__)


class UserAuthMethod:
    """This class defines methods to authenticate users with sync and async support."""

    def __init__(self, model):
        self.model = model

    # Asynchronous methods
    async def find_by_email(self, db: AsyncSession, email: str):
        """This function will return the email object with role relationship loaded (asynchronous)"""

        # Eager load role relationship for serialization
        stmt = (
            select(self.model)
            .options(selectinload(self.model.role))
            .filter(self.model.email == email)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_username(self, db: AsyncSession, username: str):
        """This function will return the username object (asynchronous)"""
        stmt = select(self.model).filter(self.model.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_with_role(self, db: AsyncSession, user_id: int):
        """This function will return the user object by ID with role relationship loaded (asynchronous)"""

        stmt = (
            select(self.model)
            .options(selectinload(self.model.role))
            .options(selectinload(self.model.creator).selectinload(Users.role))
            .filter(self.model.id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(self, db: AsyncSession, entity_id: int):
        """This function will return the entity object by ID (asynchronous)"""
        stmt = select(self.model).filter(self.model.id == entity_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate_user(self, db: AsyncSession, email: str):
        """This function will authenticate user by email (asynchronous)"""
        stmt = select(self.model).filter(self.model.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_login(self, db: AsyncSession, user_id: int):
        """This function updates the last login timestamp for a user (asynchronous)"""
        try:
            stmt = select(self.model).filter(self.model.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                # Update last_login if the field exists
                if hasattr(user, "last_login"):
                    user.last_login = datetime.now()
                await db.commit()
                return True
            return False
        except Exception:
            await db.rollback()
            return False

    async def create_user(self, db: AsyncSession, user_data: dict):
        """This function creates a new user (asynchronous)"""
        try:
            new_user = self.model(**user_data)
            db.add(new_user)
            await db.flush()

            # Reload user with role relationship using ID
            stmt = (
                select(self.model)
                .options(selectinload(self.model.role))
                .filter(self.model.id == new_user.id)
            )
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            await db.commit()
            return user
        except Exception:
            await db.rollback()
            raise

    async def update_user_by_id(self, db: AsyncSession, user_id: int, update_data: dict):
        """This function updates user data by ID with role relationship loaded (asynchronous)"""
        try:
            stmt = select(self.model).filter(self.model.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Update only provided fields
            for key, value in update_data.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)

            await db.flush()

            # Reload user with role relationship
            stmt = (
                select(self.model)
                .options(selectinload(self.model.role))
                .filter(self.model.id == user.id)
            )
            result = await db.execute(stmt)
            updated_user = result.scalar_one_or_none()

            await db.commit()
            return updated_user
        except Exception:
            await db.rollback()
            raise

    async def soft_delete_user_by_id(self, db: AsyncSession, user_id: int):
        """This function soft deletes a user by ID by setting status to deleted and deleted_at timestamp (asynchronous)"""
        try:
       

            stmt = select(self.model).filter(self.model.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            user.status = Status.DELETED
            user.deleted_at = datetime.utcnow()

            await db.commit()
            return user
        except Exception:
            await db.rollback()
            raise

    async def change_password_by_id(self, db: AsyncSession, user_id: int, hashed_password: str):
        """This function changes user password by ID (updated_at will be automatically updated) (asynchronous)"""
        try:
            stmt = select(self.model).filter(self.model.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Update password (updated_at will be automatically updated by TimestampMixin)
            user.hashed_password = hashed_password

            # Update status to ACTIVE if it was PENDING
            if user.status == Status.PENDING:
                user.status = Status.ACTIVE

            await db.flush()

            # Reload user with role relationship
            stmt = (
                select(self.model)
                .options(selectinload(self.model.role))
                .filter(self.model.id == user.id)
            )
            result = await db.execute(stmt)
            updated_user = result.scalar_one_or_none()

            await db.commit()
            return updated_user
        except Exception:
            await db.rollback()
            raise

    async def list_users(
        self,
        db: AsyncSession,
        role_id: int = None,
        status_filter: str = None,
        search: str = None,
        page: int = 1,
        limit: int = 10,
    ):
        """This function lists users with filters and pagination (asynchronous)"""
        try:
            # Build base query with role relationship
            stmt = select(self.model).options(
                selectinload(self.model.role), selectinload(self.model.creator)
            )

            # Apply filters
            if role_id:
                stmt = stmt.filter(self.model.role_id == role_id)

            if status_filter:
                try:
                    status_enum = Status(status_filter.lower())
                    stmt = stmt.filter(self.model.status == status_enum)
                except ValueError:
                    # Invalid status, return empty result
                    return [], 0

            # Search filter (name or email)
            if search:
                search_pattern = f"%{search}%"
                stmt = stmt.filter(
                    or_(
                        self.model.name.ilike(search_pattern),
                        self.model.email.ilike(search_pattern),
                    )
                )

            # Exclude deleted users by default (unless status filter is deleted)
            if not status_filter or status_filter.lower() != "deleted":
                stmt = stmt.filter(
                    or_(
                        self.model.status != Status.DELETED,
                        self.model.deleted_at.is_(None),
                    )
                )

            # Get total count - build count query with same filters
            count_stmt = select(func.count(self.model.id))
            if role_id:
                count_stmt = count_stmt.filter(self.model.role_id == role_id)
            if status_filter:
                try:
                    status_enum = Status(status_filter.lower())
                    count_stmt = count_stmt.filter(self.model.status == status_enum)
                except ValueError:
                    return [], 0
            if search:
                search_pattern = f"%{search}%"
                count_stmt = count_stmt.filter(
                    or_(
                        self.model.name.ilike(search_pattern),
                        self.model.email.ilike(search_pattern),
                    )
                )
            if not status_filter or status_filter.lower() != "deleted":
                count_stmt = count_stmt.filter(
                    or_(
                        self.model.status != Status.DELETED,
                        self.model.deleted_at.is_(None),
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
            users = result.scalars().all()

            return list(users), total
        except Exception:
            await db.rollback()
            raise

    async def fetch_deal_metrics(self, db: AsyncSession) -> dict:
        """
        Calculate deal/inquiry metrics. Falls back to 0 if tables/columns are missing.
        """
        deals_tbl = table("deals", column("OPENED"), column("STAGE_ID"))
        leads_tbl = table("leads")

        total_deals = await self._scalar_select(db, select(func.count()).select_from(deals_tbl))
        total_leads = await self._scalar_select(db, select(func.count()).select_from(leads_tbl))
        active_deals = await self._scalar_select(
            db,
            select(func.count())
            .select_from(deals_tbl)
            .where(func.upper(func.coalesce(deals_tbl.c.OPENED, "N")) == "Y"),
        )
        deals_won = await self._scalar_select(
            db,
            select(func.count())
            .select_from(deals_tbl)
            .where(func.upper(func.coalesce(deals_tbl.c.STAGE_ID, "")).like("%WON%")),
        )

        return {
            "total_inquiry": (total_deals or 0) + (total_leads or 0),
            "active_deals": active_deals or 0,
            "deals_won": deals_won or 0,
        }

    async def _scalar_select(self, db: AsyncSession, stmt) -> int:
        """
        Execute a scalar selectable and return integer result, defaulting to 0 on error.
        """
        try:
            result = await db.execute(stmt)
            value = result.scalar()
            return int(value) if value is not None else 0
        except Exception as exc:
            logger.warning(f"Metric query failed: {exc}")
            return 0

    async def find_by_reset_token(self, db: AsyncSession, reset_token: str):
        """This function will return the user object by reset token (asynchronous)"""
        stmt = (
            select(self.model)
            .filter(self.model.reset_token == reset_token)
            .filter(self.model.reset_token_expires_at > datetime.utcnow())
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def clear_reset_token_by_id(self, db: AsyncSession, user_id: int):
        """This function will clear the reset token for a user by ID (asynchronous)"""
        try:
            stmt = select(self.model).filter(self.model.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                user.reset_token = None
                user.reset_token_expires_at = None
                await db.commit()
                return True
        except Exception:
            await db.rollback()
            return False

    async def generate_reset_token_by_id(
        self, db: AsyncSession, user_id: int, reset_token: str, expires_at
    ):
        """This function generates and stores password reset token by ID (asynchronous)"""
        try:
            stmt = select(self.model).filter(self.model.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return False

            # Store reset token and expiration
            user.reset_token = reset_token
            user.reset_token_expires_at = expires_at

            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False

    async def count_active_users_by_role(self, db: AsyncSession, role_name: str) -> int:
        """
        Count users for a given role name.
        Counts all users where user.role_id == role.id and excludes deleted users.

        Args:
            db: Database session
            role_name: Name of the role to count users for

        Returns:
            Count of users with the specified role (excluding deleted users)
        """
        # First, get the role by name to get its ID
        role_stmt = select(Roles).where(func.lower(Roles.name) == role_name.lower())
        role_result = await db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        
        if not role:
            return 0
        
        # Count users by role_id, excluding deleted users
        stmt = (
            select(func.count(Users.id))
            .where(
                Users.role_id == role.id,
                or_(
                    Users.status != Status.DELETED,
                    Users.deleted_at.is_(None),
                ),
            )
        )

        result = await db.execute(stmt)
        count = result.scalar()
        return count or 0

    async def get_module_names_by_ids(self, db: AsyncSession, module_ids: list) -> list:
        """
        Fetch module slugs by their IDs.

        Args:
            db: Database session
            module_ids: List of module IDs (can be strings or integers)

        Returns:
            List of module slugs
        """
        if not module_ids:
            return []

        try:
            from apps.v1.api.auth.models.model import Modules

            # Convert all IDs to integers
            int_ids = []
            for module_id in module_ids:
                try:
                    int_ids.append(int(module_id))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid module ID format: {module_id}")
                    continue

            if not int_ids:
                return []

            # Fetch modules by IDs
            stmt = select(Modules).where(Modules.id.in_(int_ids))
            result = await db.execute(stmt)
            modules = result.scalars().all()

            # Return module slugs in the same order as IDs
            module_map = {module.id: module.slug for module in modules}
            module_slugs = []
            for module_id in int_ids:
                if module_id in module_map:
                    module_slugs.append(module_map[module_id])

            return module_slugs
        except Exception as exc:
            logger.error(f"Error fetching module slugs: {exc}", exc_info=True)
            return []

    async def get_inquiries_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> list:
        """
        Select all requests where request.assigned_by == user_id.
        
        Args:
            db: Database session
            user_id: User ID to filter requests by assigned_by
            
        Returns:
            List of Requests objects assigned to the user
        """
        stmt = (
            select(Requests)
            .options(
                selectinload(Requests.company),
                selectinload(Requests.current_stage),
                selectinload(Requests.request_stage_activities).selectinload(
                    RequestStageActivity.stage
                ),
            )
            .where(Requests.assigned_by == user_id)
            .order_by(Requests.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def fetch_user_inquiry_metrics(
        self, db: AsyncSession, user_id: int
    ) -> dict:
        """
        Calculate inquiry metrics for a specific user.
        
        Args:
            db: Database session
            user_id: User ID to calculate metrics for
            
        Returns:
            Dictionary with total_inquiries, active_deals, deals_won counts
        """
        try:
       

            # Total inquiries assigned to user
            total_stmt = (
                select(func.count(Requests.id))
                .where(Requests.assigned_by == user_id)
            )
            total_result = await db.execute(total_stmt)
            total_inquiries = total_result.scalar() or 0

            # Active deals (phase == DEAL and status == ACTIVE)
            active_stmt = (
                select(func.count(Requests.id))
                .where(
                    Requests.assigned_by == user_id,
                    Requests.phase == RequestPhase.DEAL,
                    Requests.request_status == RequestStatus.ACTIVE,
                )
            )
            active_result = await db.execute(active_stmt)
            active_deals = active_result.scalar() or 0

            # Deals won (phase == DEAL and status == COMPLETED)
            won_stmt = (
                select(func.count(Requests.id))
                .where(
                    Requests.assigned_by == user_id,
                    Requests.phase == RequestPhase.DEAL,
                    Requests.request_status == RequestStatus.COMPLETED,
                )
            )
            won_result = await db.execute(won_stmt)
            deals_won = won_result.scalar() or 0

            return {
                "total_inquiry": total_inquiries,
                "active_deals": active_deals,
                "deals_won": deals_won,
            }
        except Exception as exc:
            logger.warning(f"User inquiry metrics query failed: {exc}")
            return {
                "total_inquiry": 0,
                "active_deals": 0,
                "deals_won": 0,
            }

    async def get_profile_by_user_id(self, db: AsyncSession, user_id: int):
        """This function returns user profile by ID with role relationship loaded (asynchronous)
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object with role relationship loaded, or None if not found
        """
        stmt = (
            select(self.model)
            .options(selectinload(self.model.role))
            .filter(self.model.id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_profile_by_user_id(
        self, db: AsyncSession, user_id: int, update_data: dict
    ):
        """This function updates user profile data by ID with role relationship loaded (asynchronous)
        
        Only allows updating profile fields: name, phone_number, location, profile_image_url.
        Does not allow updating: role_id, status, email, password, or other sensitive fields.
        
        Args:
            db: Database session
            user_id: User ID
            update_data: Dictionary with fields to update (only allowed fields)
            
        Returns:
            Updated user object with role relationship loaded, or None if not found
        """
        try:
            stmt = select(self.model).filter(self.model.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Update only provided fields that are allowed
            allowed_fields = ["name", "phone_number", "location", "profile_image_url"]
            for key, value in update_data.items():
                if key in allowed_fields and hasattr(user, key):
                    setattr(user, key, value)

            await db.flush()

            # Reload user with role relationship
            stmt = (
                select(self.model)
                .options(selectinload(self.model.role))
                .filter(self.model.id == user.id)
            )
            result = await db.execute(stmt)
            updated_user = result.scalar_one_or_none()

            await db.commit()
            return updated_user
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    def calculate_profile_completeness(user) -> int:
        """Calculate profile completeness percentage.
        
        Args:
            user: User object
            
        Returns:
            Integer percentage (0-100) representing profile completeness
        """
        fields_to_check = {
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number,
            "location": user.location,
            "profile_image_url": user.profile_image_url,
        }
        
        completed_fields = sum(1 for value in fields_to_check.values() if value)
        total_fields = len(fields_to_check)
        
        if total_fields == 0:
            return 0
        
        completeness = int((completed_fields / total_fields) * 100)
        return completeness