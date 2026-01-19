"""
Helper class for supplier operations.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime

from sqlalchemy import select, func, update, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.v1.api.products.models.model import Products, Categories
from apps.v1.api.suppliers.models.model import Suppliers, ProductSupplierMapping, Documents
from apps.v1.api.suppliers.models.attribute import SourceTable
from core.utils.pagination import Params

logger = logging.getLogger(__name__)


class SupplierMethods:
    """Utility and data-access methods for suppliers."""

    @staticmethod
    def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def resolve_params(params: Params) -> Params:
        if params.size is None:
            params.size = 10
        if params.page is None or params.page < 1:
            params.page = 1
        return params

    @staticmethod
    def parse_filter(
        filter_raw: Optional[str] = None,
        name_filter: Optional[str] = None,
        country_filter: Optional[str] = None,
        search: Optional[str] = None,
        company_type: Optional[str] = None,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        child_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        filters: Dict[str, Any] = {}
        if filter_raw:
            try:
                if isinstance(filter_raw, str):
                    filters.update(json.loads(filter_raw))
                elif isinstance(filter_raw, dict):
                    filters.update(filter_raw)
            except (json.JSONDecodeError, TypeError):
                pass
        if search:
            filters["search"] = search
        if name_filter:
            filters["company_name"] = name_filter
        if country_filter:
            filters["country"] = country_filter
        if company_type:
            filters["company_type"] = company_type
        if category:
            filters["category"] = category
        if sub_category:
            filters["sub_category"] = sub_category
        if child_category:
            filters["child_category"] = child_category
        return filters

    @staticmethod
    async def count_suppliers(db: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        # Use subquery to get distinct supplier IDs first, then count
        subquery = select(Suppliers.id).where(Suppliers.deleted_at.is_(None)).distinct()
        subquery = SupplierMethods._apply_filters(subquery, filters, is_count=True)
        stmt = select(func.count()).select_from(subquery.subquery())
        result = await db.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def fetch_supplier_page(
        db: AsyncSession,
        params: Params,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[Suppliers]:
        stmt = select(Suppliers).where(Suppliers.deleted_at.is_(None))
        stmt = SupplierMethods._apply_filters(stmt, filters, is_count=False)
        stmt = stmt.distinct()
        stmt = SupplierMethods._apply_sorting(stmt, sort_by, sort_order)
        stmt = stmt.offset((params.page - 1) * params.size).limit(params.size)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _apply_filters(stmt, filters: Optional[Dict[str, Any]] = None, is_count: bool = False):
        if not filters:
            return stmt

        # Determine if we need product joins for category filtering
        has_category_filter = any(
            filters.get(key) for key in ["category", "sub_category", "child_category"]
        )

        if has_category_filter:
            stmt = (
                stmt.join(
                    ProductSupplierMapping,
                    ProductSupplierMapping.supplier_id == Suppliers.id,
                    isouter=True,
                )
                .join(
                    Products,
                    Products.id == ProductSupplierMapping.product_id,
                    isouter=True,
                )
                .join(
                    Categories,
                    or_(
                        Categories.id == Products.category_id,
                        Categories.id == Products.sub_category_id,
                        Categories.id == Products.parent_category_id,
                    ),
                    isouter=True,
                )
            )

        # Search filter (uuid, name, email)
        if "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            try:
                search_id = int(filters["search"])
                stmt = stmt.where(
                    or_(
                        Suppliers.id == search_id,
                        Suppliers.company_name.ilike(search_term),
                        Suppliers.supplier_name.ilike(search_term),
                        Suppliers.email.ilike(search_term),
                    )
                )
            except (ValueError, TypeError):
                stmt = stmt.where(
                    or_(
                        Suppliers.company_name.ilike(search_term),
                        Suppliers.supplier_name.ilike(search_term),
                        Suppliers.email.ilike(search_term),
                    )
                )

        # Company name filter
        if "company_name" in filters and filters["company_name"]:
            stmt = stmt.where(Suppliers.company_name.ilike(f"%{filters['company_name']}%"))

        # Country filter
        if "country" in filters and filters["country"]:
            stmt = stmt.where(Suppliers.country.ilike(f"%{filters['country']}%"))

        # Company type filter
        if "company_type" in filters and filters["company_type"]:
            stmt = stmt.where(Suppliers.company_type.ilike(f"%{filters['company_type']}%"))

        # Product category filter
        if "category" in filters and filters["category"]:
            category_pattern = f"%{filters['category']}%"
            stmt = stmt.where(
                or_(
                    Categories.name.ilike(category_pattern),
                    Products.product_category.ilike(category_pattern),
                    Suppliers.product_category.ilike(category_pattern),
                )
            )

        # Sub category filter
        if "sub_category" in filters and filters["sub_category"]:
            sub_category_pattern = f"%{filters['sub_category']}%"
            stmt = stmt.where(
                or_(
                    Categories.name.ilike(sub_category_pattern),
                    Products.product_category.ilike(sub_category_pattern),
                )
            )

        # Child category filter
        if "child_category" in filters and filters["child_category"]:
            child_category_pattern = f"%{filters['child_category']}%"
            stmt = stmt.where(
                or_(
                    Categories.name.ilike(child_category_pattern),
                    Products.product_category.ilike(child_category_pattern),
                )
            )

        return stmt

    @staticmethod
    def _apply_sorting(stmt, sort_by: Optional[str] = None, sort_order: Optional[str] = None):
        """Apply sorting to the query."""
        if sort_by:
            if sort_by == "created_at":
                sort_column = Suppliers.created_at
            elif sort_by == "updated_at":
                sort_column = Suppliers.updated_at
            else:
                sort_column = Suppliers.created_at

            if sort_order and sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(Suppliers.created_at.desc())
        return stmt

    @staticmethod
    async def bulk_insert_suppliers(db: AsyncSession, records: List[Dict[str, Any]]) -> None:
        supplier_instances = [Suppliers(**record) for record in records]
        db.add_all(supplier_instances)
        await db.commit()

    @staticmethod
    async def get_supplier_by_id(db: AsyncSession, supplier_id: int) -> Optional[Suppliers]:
        stmt = select(Suppliers).where(
            and_(Suppliers.id == supplier_id, Suppliers.deleted_at.is_(None))
        ).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_supplier_record(
        db: AsyncSession, supplier_id: int, clean_data: Dict[str, Any]
    ) -> bool:
        stmt = update(Suppliers).where(Suppliers.id == supplier_id).values(**clean_data)
        result = await db.execute(stmt)
        if result.rowcount == 0:
            return False
        await db.commit()
        return True

    @staticmethod
    async def create_supplier_record(db: AsyncSession, clean_data: Dict[str, Any]) -> Suppliers:
        supplier = Suppliers(**clean_data)
        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)
        return supplier


load_json_file = SupplierMethods.load_json_file
resolve_params = SupplierMethods.resolve_params
parse_filter = SupplierMethods.parse_filter
count_suppliers = SupplierMethods.count_suppliers
fetch_supplier_page = SupplierMethods.fetch_supplier_page
bulk_insert_suppliers = SupplierMethods.bulk_insert_suppliers
get_supplier_by_id = SupplierMethods.get_supplier_by_id
update_supplier_record = SupplierMethods.update_supplier_record
create_supplier_record = SupplierMethods.create_supplier_record


class SupplierMethod:
    """Database query methods for Suppliers model."""

    def __init__(self, model):
        self.model = model

    async def list_suppliers(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        country: Optional[str] = None,
        company_type: Optional[str] = None,
        category_id: Optional[int] = None,
        sub_category_id: Optional[int] = None,
        child_category_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[Suppliers], int]:
        """
        List suppliers with filters, sorting, and pagination.
        Returns suppliers list and total count.

        Args:
            db: Database session
            search: Search by uuid, name, or email
            country: Filter by country
            company_type: Filter by company type
            category_id: Filter by category id (1, 2, 3, etc.)
            sub_category_id: Filter by sub_category id (1, 2, 3, etc.)
            child_category_id: Filter by child_category id (1, 2, 3, etc.)
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            sort_by: Field to sort by (created_at, updated_at)
            sort_order: Sort order (asc, desc)
            page: Page number
            limit: Items per page

        Returns:
            Tuple of (suppliers list, total count)
        """
        # Build base query with relationships
        query = select(self.model).options(
            selectinload(Suppliers.product_suppliers).selectinload(ProductSupplierMapping.product),
        ).filter(self.model.deleted_at.is_(None))

        # Build filters
        filters = []

        # Search filter (uuid, company_name, supplier_name, email)
        if search:
            search_term = f"%{search}%"
            try:
                search_id = int(search)
                search_filters = [
                    Suppliers.id == search_id,
                    Suppliers.company_name.ilike(search_term),
                    Suppliers.supplier_name.ilike(search_term),
                    Suppliers.email.ilike(search_term),
                ]
            except (ValueError, TypeError):
                search_filters = [
                    Suppliers.company_name.ilike(search_term),
                    Suppliers.supplier_name.ilike(search_term),
                    Suppliers.email.ilike(search_term),
                ]
            filters.append(or_(*search_filters))

        # Country filter
        if country:
            filters.append(Suppliers.country.ilike(f"%{country}%"))

        # Company type filter
        if company_type:
            filters.append(Suppliers.company_type.ilike(f"%{company_type}%"))

        # Category filters (require joins)
        if category_id or sub_category_id or child_category_id:
            query = query.join(
                ProductSupplierMapping,
                ProductSupplierMapping.supplier_id == Suppliers.id,
                isouter=True,
            ).join(
                Products,
                Products.id == ProductSupplierMapping.product_id,
                isouter=True,
            )

            if category_id:
                # Filter by parent category
                category_subquery = select(Categories.id).filter(Categories.id == category_id)
                filters.append(
                    or_(
                        Products.parent_category_id.in_(category_subquery),
                    )
                )

            if sub_category_id:
                # Filter by sub category
                sub_category_subquery = select(Categories.id).filter(
                    Categories.id == sub_category_id
                )
                filters.append(Products.sub_category_id.in_(sub_category_subquery))

            if child_category_id:
                # Filter by child category
                child_category_subquery = select(Categories.id).filter(
                    Categories.id == child_category_id
                )
                filters.append(Products.category_id.in_(child_category_subquery))

        # Date range filter
        if start_date or end_date:
            if start_date and end_date:
                # Both dates provided - filter between dates
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                filters.append(Suppliers.created_at.between(start_datetime, end_datetime))
            elif start_date:
                # Only start date - filter from start date onwards
                start_datetime = datetime.combine(start_date, datetime.min.time())
                filters.append(Suppliers.created_at >= start_datetime)
            elif end_date:
                # Only end date - filter up to end date
                end_datetime = datetime.combine(end_date, datetime.max.time())
                filters.append(Suppliers.created_at <= end_datetime)

        # Apply filters
        if filters:
            query = query.where(and_(*filters))

        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Sorting
        if sort_by:
            sort_column = getattr(Suppliers, sort_by, None)
            if sort_column:
                if sort_order and sort_order.lower() == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(Suppliers.created_at))
        else:
            query = query.order_by(desc(Suppliers.created_at))

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        suppliers = result.scalars().all()

        return list(suppliers), total

    async def get_categories_map(
        self, db: AsyncSession, category_ids: List[int]
    ) -> Dict[int, Categories]:
        """
        Fetch categories by IDs and return as a map.

        Args:
            db: Database session
            category_ids: List of category IDs

        Returns:
            Dictionary mapping category ID to Categories object
        """
        if not category_ids:
            return {}

        categories_query = select(Categories).filter(Categories.id.in_(category_ids))
        categories_result = await db.execute(categories_query)
        return {cat.id: cat for cat in categories_result.scalars().all()}

    async def find_by_id(
        self,
        db: AsyncSession,
        supplier_id: int,
    ) -> Optional[Suppliers]:
        """
        Find supplier by ID with all relationships loaded using selectinload.

        Args:
            db: Database session
            supplier_id: ID of the supplier to retrieve

        Returns:
            Suppliers model instance with relationships or None
        """
        try:
            # Convert supplier_id to int if it's a string
            if isinstance(supplier_id, str):
                supplier_id = int(supplier_id)

            # Build query with eager loading of relationships
            stmt = (
                select(self.model)
                .options(
                    selectinload(Suppliers.product_suppliers).selectinload(
                        ProductSupplierMapping.product
                    ),
                    selectinload(Suppliers.assigned_by_user),
                    selectinload(Suppliers.generated_by_user),
                    selectinload(Suppliers.updated_by_user),
                )
                .filter(self.model.id == supplier_id)
                .filter(self.model.deleted_at.is_(None))
            )

            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting supplier_id to int: {e}")
            return None
        except Exception as e:
            logger.error(f"Error finding supplier by id: {e}", exc_info=True)
            return None


class DocumentRepository:
    """Repository class for Document database operations."""

    @staticmethod
    async def get_documents_by_source(
        db: AsyncSession, source_table: SourceTable, mapping_id: int
    ) -> List[Documents]:
        """
        Fetch documents by source table and mapping ID.

        Args:
            db: Database session
            source_table: Source table enum (e.g., SourceTable.PRODUCTS)
            mapping_id: ID of the mapped entity

        Returns:
            List[Documents]: List of matching documents
        """
        stmt = select(Documents).where(
            and_(
                Documents.source_table == source_table,
                Documents.mapping_id == mapping_id,
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
