"""
Database query methods for request models.
"""

import logging
from typing import Optional, Dict, List, Any
from sqlalchemy import func, desc, asc, and_, select, cast, String, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.v1.api.request.models.model import (
    Requests,
    Stage,
    RequestProductsMapping,
    RequestStageActivity,
    RequestCustomersMapping,
)
from apps.v1.api.auth.models.model import Users
from apps.v1.api.suppliers.models.model import Documents
from apps.v1.api.email_collection.models.model import Emails
from datetime import datetime
from apps.v1.api.request.models.attribute import RequestPhase, RequestStatus, StagePhase
from apps.v1.api.products.models.model import Products, Categories
from apps.v1.api.customer.models.model import Customers

logger = logging.getLogger(__name__)


class RequestMethod:
    """Database query methods for Requests model."""

    def __init__(self, model):
        self.model = model

    async def find_by_id(
        self,
        db: AsyncSession,
        request_id: str,
        current_user: Users = None,
    ) -> Optional[Requests]:
        """
        Find request by UUID with all relationships loaded using joinload/selectinload.

        Args:
            db: Database session
            request_id: UUID of the request to retrieve (using id as uuid)

        Returns:
            Requests model instance with relationships or None
        """
        try:
            # Convert uuid string to int if it's numeric, otherwise use as is
            try:
                request_id = int(request_id)
            except ValueError:
                # If not numeric, try to find by deal_id or name
                request_id = None

            stmt = select(self.model)
            # if current_user.role.name == "Staff":
            #     stmt = stmt.filter(self.model.assigned_by == current_user.id)

            # Exclude soft-deleted records
            stmt = stmt.filter(self.model.deleted_at.is_(None))

            # Build filter condition
            stmt = stmt.options(
                # Load company relationship
                selectinload(self.model.company),
                # Load request customers with customer relationship
                selectinload(self.model.request_customers).selectinload(
                    RequestCustomersMapping.customer
                ),
                #selectinload(self.model.stages),
                # Load request stage activities relationship with stage
                selectinload(self.model.request_stage_activities).selectinload(
                    RequestStageActivity.stage
                ),
                # Load current and next stage
                selectinload(self.model.current_stage),
                selectinload(self.model.next_stage),
                # Load request products with product relationship and categories
                selectinload(self.model.request_products).selectinload(
                    RequestProductsMapping.product
                ),
                # Load assigned_to user with role
                selectinload(self.model.assigned_to).selectinload(Users.role),
            ).filter(self.model.id == request_id)

            result = await db.execute(stmt)
            request = result.scalar_one_or_none()

            if not request:
                return None

            # Load documents separately (using mapping_id and source_table)
            documents_stmt = select(Documents).filter(
                and_(Documents.mapping_id == request.id, Documents.source_table == "requests")
            )
            documents_result = await db.execute(documents_stmt)
            request._documents = list(documents_result.scalars().all())

            # Load emails separately (using mapping_id and mapping_table)
            emails_stmt = select(Emails).filter(
                and_(
                    Emails.mapping_id == str(request.id),
                    Emails.mapping_table == "request",
                )
            )
            emails_result = await db.execute(emails_stmt)
            request._emails = list(emails_result.scalars().all())

            # Load users (responsible, created_by, modified_by, observers)
            user_ids_to_load = set()
            if request.responsible_person:
                user_ids_to_load.add(("bitrix_id", request.responsible_person))
            if request.created_by:
                user_ids_to_load.add(("id", request.created_by))
            if request.modified_by:
                user_ids_to_load.add(("id", request.modified_by))
            if request.observer_ids:
                if isinstance(request.observer_ids, list):
                    user_ids_to_load.update([("id", uid) for uid in request.observer_ids if uid])

            # Load all users in one query
            if user_ids_to_load:
                user_id_list = [uid for _, uid in user_ids_to_load if _ == "id"]
                user_bitrix_id_list = [uid for _, uid in user_ids_to_load if _ == "bitrix_id"]

                users_stmt = select(Users).options(selectinload(Users.role))
                user_filters = []
                if user_id_list:
                    user_filters.append(Users.id.in_(user_id_list))
                if user_bitrix_id_list:
                    user_filters.append(Users.bitrix_id.in_(user_bitrix_id_list))

                if user_filters:
                    users_stmt = users_stmt.filter(or_(*user_filters))
                    users_result = await db.execute(users_stmt)
                    request._all_users = {u.id: u for u in users_result.scalars().all()}
                    request._all_users_by_bitrix = {
                        u.bitrix_id: u for u in request._all_users.values() if u.bitrix_id
                    }
                else:
                    request._all_users = {}
                    request._all_users_by_bitrix = {}
            else:
                request._all_users = {}
                request._all_users_by_bitrix = {}

            return request
        except Exception as exc:
            logger.error(f"Error finding request by UUID: {exc}", exc_info=True)
            raise

    async def list_requests(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        priority: Optional[str] = None,
        phase: Optional[str] = None,
        request_status: Optional[str] = None,
        stage_id: Optional[int] = None,
        user_id: Optional[int] = None,
        country: Optional[str] = None,
        customer_id: Optional[int] = None,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
        current_user: Users = None,
    ):
        """
        List requests with filtering, sorting, pagination, and phase counts.

        Args:
            db: Database session
            search: Search by uuid, customer_name, customer_email, bitrix_url, bitrix_id
            priority: Filter by priority (urgent, high, medium, low)
            phase: Filter by phase (lead, deal, registration)
            request_status: Filter by status (active, inactive)
            stage_id: Filter by stage id
            user_id: Filter by user id
            country: Filter by country
            customer_id: Filter by customer id
            product_id: Filter by product id
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
            sort_by: Sort by field (created_at, updated_at)
            sort_order: Sort order (asc, desc)
            page: Page number
            limit: Items per page

        Returns:
            Tuple of (requests list, total count, data counts dict)
        """
        try:
            # Build base query with relationships
            query = select(self.model).options(
                selectinload(self.model.company),
                selectinload(self.model.current_stage),
                selectinload(self.model.assigned_to),
                selectinload(self.model.request_customers).selectinload(
                    RequestCustomersMapping.customer
                ),
                selectinload(self.model.request_products).selectinload(
                    RequestProductsMapping.product
                ),
                # Load request stage activities with stage relationship
                selectinload(self.model.request_stage_activities).selectinload(
                    RequestStageActivity.stage
                ),
            )

            # Exclude soft-deleted records
            query = query.filter(self.model.deleted_at.is_(None))

            if current_user.role.name == "Staff":
                query = query.filter(self.model.assigned_by == current_user.id)

            # Build filters
            filters = self._build_filters(
                search=search,
                priority=priority,
                phase=phase,
                request_status=request_status,
                stage_id=stage_id,
                user_id=user_id,
                country=country,
                customer_id=customer_id,
                product_id=product_id,
                start_date=start_date,
                end_date=end_date,
            )

            # Apply filters
            if filters:
                query = query.where(and_(*filters))

            # Get total count before pagination
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0

            # Get data counts by phase (all, lead, deal, registration)
            data_counts = await self._get_phase_counts(
                db=db,
                search=search,
                priority=priority,
                request_status=request_status,
                stage_id=stage_id,
                user_id=user_id,
                country=country,
                customer_id=customer_id,
                product_id=product_id,
                start_date=start_date,
                end_date=end_date,
                current_user=current_user,
            )

            # Sorting
            if sort_by:
                sort_column = getattr(self.model, sort_by, None)
                if sort_column:
                    if sort_order and sort_order.lower() == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))
                else:
                    query = query.order_by(desc(self.model.created_at))
            else:
                query = query.order_by(desc(self.model.created_at))

            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)

            # Execute query
            result = await db.execute(query)
            requests = result.scalars().all()
            for request in requests:
                request.customer_company_name = (
                    request.request_customers[0].customer.company_name
                    if request.request_customers
                    else None
                )

            return list(requests), total, data_counts

        except Exception as exc:
            logger.error(f"Error listing requests: {exc}", exc_info=True)
            raise

    def _build_filters(
        self,
        search: Optional[str] = None,
        priority: Optional[str] = None,
        phase: Optional[str] = None,
        request_status: Optional[str] = None,
        stage_id: Optional[int] = None,
        user_id: Optional[int] = None,
        country: Optional[str] = None,
        customer_id: Optional[int] = None,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """Build filter conditions for requests query."""

        filters = []

        # Search filter (uuid, customer_name, customer_email, bitrix_url, bitrix_id)
        if search:
            search_term = f"%{search}%"
            search_filters = [
                cast(self.model.id, String).ilike(search_term),
                self.model.name.ilike(search_term),
                self.model.bitrix_url.ilike(search_term),
                cast(self.model.bitrix_id, String).ilike(search_term),
            ]
            # Add customer search via subquery
            customer_subquery = (
                select(RequestCustomersMapping.request_id)
                .join(Customers, RequestCustomersMapping.customer_id == Customers.id)
                .filter(
                    or_(
                        Customers.company_name.ilike(search_term),
                        (
                            Customers.email_ids.contains(search_term)
                            if hasattr(Customers, "email_ids")
                            else False
                        ),
                    )
                )
            )
            search_filters.append(self.model.id.in_(customer_subquery))
            filters.append(or_(*search_filters))

        # Priority filter
        if priority:
            filters.append(self.model.urgency_level == priority)

        # Phase filter
        if phase:
            try:
                phase_enum = RequestPhase[phase.upper()]
                filters.append(self.model.phase == phase_enum)
            except (KeyError, AttributeError):
                filters.append(cast(self.model.phase, String) == phase.lower())

        # Status filter
        if request_status:
            try:
                request_status_enum = RequestStatus[request_status.upper()]
                filters.append(self.model.request_status == request_status_enum)
            except (KeyError, AttributeError):
                filters.append(cast(self.model.request_status, String) == request_status.lower())

        # User id filter
        if user_id:
            user_subquery = (
                select(self.model.id)
                .join(Users, self.model.assigned_by == Users.id)
                .filter(Users.id == user_id)
            )
            filters.append(self.model.id.in_(user_subquery))

        # Country filter
        if country:
            country_list = [c.strip() for c in country.split(",")]
            country_filters = [self.model.country.ilike(f"%{c}%") for c in country_list]
            customer_country_subquery = (
                select(RequestCustomersMapping.request_id)
                .join(Customers, RequestCustomersMapping.customer_id == Customers.id)
                .filter(or_(*[Customers.country.ilike(f"%{c}%") for c in country_list]))
            )
            country_filters.append(self.model.id.in_(customer_country_subquery))
            filters.append(or_(*country_filters))

        # Customer id filter
        if customer_id:
            customer_subquery = (
                select(RequestCustomersMapping.request_id)
                .join(Customers, RequestCustomersMapping.customer_id == Customers.id)
                .filter(Customers.id == customer_id)
            )
            filters.append(self.model.id.in_(customer_subquery))

        # Product id filter
        if product_id:
            product_subquery = (
                select(RequestProductsMapping.request_id)
                .join(Products, RequestProductsMapping.product_id == Products.id)
                .filter(Products.id == product_id)
            )
            filters.append(self.model.id.in_(product_subquery))

        # Date range filter
        if start_date or end_date:
            try:
                if start_date and end_date:
                    start_dt = datetime.fromisoformat(start_date)
                    end_dt = datetime.fromisoformat(end_date)
                    filters.append(self.model.created_at.between(start_dt, end_dt))
                elif start_date:
                    start_dt = datetime.fromisoformat(start_date)
                    filters.append(self.model.created_at >= start_dt)
                elif end_date:
                    end_dt = datetime.fromisoformat(end_date)
                    filters.append(self.model.created_at <= end_dt)
            except ValueError as e:
                logger.warning(
                    f"Invalid date format: start_date={start_date}, end_date={end_date}, error: {e}"
                )

        if stage_id:
            filters.append(self.model.current_stage_id == stage_id)

        return filters

    async def _get_phase_counts(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        priority: Optional[str] = None,
        request_status: Optional[str] = None,
        stage_id: Optional[int] = None,
        user_id: Optional[int] = None,
        country: Optional[str] = None,
        customer_id: Optional[int] = None,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        current_user: Users = None,
    ):
        """Get counts by phase (all, lead, deal, registration) with filters applied."""

        # Build base count query (same filters as main query, but exclude phase)
        base_count_query = select(self.model)

        # Exclude soft-deleted records
        base_count_query = base_count_query.filter(self.model.deleted_at.is_(None))

        # If current user is not admin, filter by assigned_by
        if current_user.role.name == "Staff":
            base_count_query = base_count_query.filter(self.model.assigned_by == current_user.id)

        # Build count filters (same as main query filters, but exclude phase)
        count_filters = self._build_filters(
            search=search,
            priority=priority,
            phase=None,  # Exclude phase filter
            request_status=request_status,
            stage_id=stage_id,
            user_id=user_id,
            country=country,
            customer_id=customer_id,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Apply joins if needed
        if stage_id:
            base_count_query = base_count_query.join(Stage, self.model.current_stage_id == Stage.id)

        # Apply count filters
        if count_filters:
            base_count_query = base_count_query.where(and_(*count_filters))

        # Count all requests (with filters applied)
        all_count_query = select(func.count()).select_from(base_count_query.subquery())
        all_count_result = await db.execute(all_count_query)
        all_count = all_count_result.scalar() or 0

        # Count by phase (apply phase filter to base query)
        lead_count_query = base_count_query.filter(self.model.phase == RequestPhase.LEAD)
        lead_count_stmt = select(func.count()).select_from(lead_count_query.subquery())
        lead_count_result = await db.execute(lead_count_stmt)
        lead_count = lead_count_result.scalar() or 0

        deal_count_query = base_count_query.filter(self.model.phase == RequestPhase.DEAL)
        deal_count_stmt = select(func.count()).select_from(deal_count_query.subquery())
        deal_count_result = await db.execute(deal_count_stmt)
        deal_count = deal_count_result.scalar() or 0

        registration_count_query = base_count_query.filter(
            self.model.phase == RequestPhase.REGISTRATION
        )
        registration_count_stmt = select(func.count()).select_from(
            registration_count_query.subquery()
        )
        registration_count_result = await db.execute(registration_count_stmt)
        registration_count = registration_count_result.scalar() or 0

        return {
            "all": all_count,
            "lead": lead_count,
            "deal": deal_count,
            "registration": registration_count,
        }

    async def get_categories_map(self, db: AsyncSession, request_ids: List[int]) -> Dict[int, Any]:
        """
        Fetch all category IDs from products associated with requests in a single optimized query.

        Args:
            db: Database session
            request_ids: List of request IDs

        Returns:
            Dictionary mapping category ID to Categories object
        """
        if not request_ids:
            return {}

        # Single query to get all category IDs from products via request_products mapping
        category_ids_query = (
            select(Products.parent_category_id, Products.sub_category_id, Products.category_id)
            .join(
                RequestProductsMapping,
                RequestProductsMapping.product_id == Products.id,
            )
            .filter(RequestProductsMapping.request_id.in_(request_ids))
            .distinct()
        )

        result = await db.execute(category_ids_query)
        rows = result.all()

        # Collect all unique category IDs
        all_category_ids = set()
        for row in rows:
            if row.parent_category_id:
                all_category_ids.add(row.parent_category_id)
            if row.sub_category_id:
                all_category_ids.add(row.sub_category_id)
            if row.category_id:
                all_category_ids.add(row.category_id)

        if not all_category_ids:
            return {}

        # Fetch all categories in one query
        categories_query = select(Categories).filter(Categories.id.in_(list(all_category_ids)))
        categories_result = await db.execute(categories_query)
        return {cat.id: cat for cat in categories_result.scalars().all()}



## Stage API Methods
class StageMethod:
    """Database query methods for Stage model."""

    async def get_all_stages(self, db: AsyncSession, phase: Optional[str] = None) -> List[Stage]:
        """
        Get all stages with next_stage relationship loaded and ordered by sequence.

        Args:
            db: Database session
            phase: Optional phase filter (lead, registration, deal)

        Returns:
            List of Stage model instances
        """
        query = (
            select(Stage)
            .options(selectinload(Stage.next_stage))
            .order_by(asc(Stage.order_sequence))
        )

        # Apply phase filter if provided
        if phase:
            try:
                # Validate phase against StagePhase enum
                stage_phase = StagePhase(phase.lower())
                # Map StagePhase to RequestPhase for database query
                # Since Stage model uses RequestPhase enum
                phase_mapping = {
                    StagePhase.LEAD: RequestPhase.LEAD,
                    StagePhase.REGISTRATION: RequestPhase.REGISTRATION,
                    StagePhase.DEAL: RequestPhase.DEAL,
                }
                request_phase = phase_mapping.get(stage_phase)
                if request_phase:
                    query = query.filter(Stage.phase == request_phase)
            except (ValueError, KeyError):
                # If phase doesn't match StagePhase enum, try direct string match
                logger.warning(f"Invalid phase value: {phase}, filtering by string match")
                query = query.filter(cast(Stage.phase, String) == phase.lower())

        result = await db.execute(query)
        return list(result.scalars().all())
