"""
Database utility methods for Product operations.
"""

import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import aliased
from datetime import date, datetime

from sqlalchemy import func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.v1.api.logistic.models.model import Logistic
from apps.v1.api.products.models.model import Categories, Products
from apps.v1.api.suppliers.models.model import (
    Documents,
    ProductSupplierMapping,
    Suppliers,
)
from apps.v1.api.auth.models.model import Users
from config.env_config import get_settings


class ProductListItem:
    """
    Data class for product list items with joined category and supplier data.

    Used to pass product objects with additional joined fields to serializer.
    """

    def __init__(
        self,
        product: Products,
        category_name: Optional[str] = None,
        parent_category_name: Optional[str] = None,
        sub_category_name: Optional[str] = None,
        primary_supplier_name: Optional[str] = None,
        doc_type: Optional[str] = None,
        category_type: Optional[str] = None,
    ):
        """
        Initialize product list item.

        Args:
            product: Products SQLAlchemy model instance
            category_name: Category name from join
            parent_category_name: Parent category name from join
            sub_category_name: Sub category name from join
            primary_supplier_name: Primary supplier name from join
            category_type: Category type from product
        """
        self.product = product
        self.category_name = category_name or ""
        self.parent_category_name = parent_category_name or ""
        self.sub_category_name = sub_category_name or ""
        self.category_type = category_type or ""
        self.doc_type = doc_type or ""
        self.primary_supplier_name = primary_supplier_name or product.supplier_name or ""


class ProductRepository:
    """Repository class for Product database operations."""

    @staticmethod
    def load_json_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Load JSON file and return list of records.

        Args:
            file_path: Path to JSON file

        Returns:
            List[Dict[str, Any]]: Parsed JSON data
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    async def count_products(db: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count total products, optionally with filters.

        Args:
            db: Database session
            filters: Optional dictionary of filter criteria

        Returns:
            int: Total product count
        """
        query = select(func.count(Products.id)).where(Products.deleted_at.is_(None))
        if filters:
            query = ProductRepository._apply_filters(query, filters)
        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def fetch_product_page(
        db: AsyncSession,
        offset: int,
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Products]:
        """
        Fetch paginated products, optionally with filters.

        Args:
            db: Database session
            offset: Pagination offset
            limit: Pagination limit
            filters: Optional dictionary of filter criteria

        Returns:
            List[Products]: List of products
        """
        query = select(Products).where(Products.deleted_at.is_(None)).offset(offset).limit(limit).order_by(Products.id)
        if filters:
            query = ProductRepository._apply_filters(query, filters)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def fetch_product_by_xml_id(db: AsyncSession, xml_id: str) -> Optional[Products]:
        """
        Fetch a single product by xml_id.

        Args:
            db: Database session
            xml_id: Product xml_id

        Returns:
            Optional[Products]: Product if found, None otherwise
        """
        result = await db.execute(
            select(Products).where(
                and_(Products.xml_id == xml_id, Products.deleted_at.is_(None))
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_product_by_id(db: AsyncSession, product_id: str) -> Optional[Products]:
        """
        Fetch a single product by ID or xml_id.

        Args:
            db: Database session
            product_id: Product ID (integer as string) or xml_id

        Returns:
            Optional[Products]: Product if found, None otherwise
        """
        # Try to parse as integer ID first
        try:
            product_id_int = int(product_id)
            result = await db.execute(
                select(Products).where(
                    and_(Products.id == product_id_int, Products.deleted_at.is_(None))
                )
            )
            product = result.scalar_one_or_none()
            if product:
                return product
        except (ValueError, TypeError):
            pass

        # Fall back to xml_id lookup
        result = await db.execute(
            select(Products).where(
                and_(Products.xml_id == product_id, Products.deleted_at.is_(None))
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _apply_filters(query, filters: Dict[str, Any]):
        """
        Apply filters to query.

        Supports partial matches for name/category, price range, certificate, and free-text.

        Args:
            query: SQLAlchemy query
            filters: Dictionary of filter criteria

        Returns:
            Modified query with filters applied
        """
        for key, value in filters.items():
            if value is None:
                continue

            # Free-text search across supported columns (name, category)
            if key == "q":
                search = f"%{value}%"
                query = query.where(
                    or_(
                        Products.name.ilike(search),
                        Products.product_category.ilike(search),
                    )
                )
                continue

            # Price range
            if key == "min_price":
                query = query.where(Products.price >= value)
                continue
            if key == "max_price":
                query = query.where(Products.price <= value)
                continue

            norm_key = ProductRepository._normalize_filter_key(key)
            if not hasattr(Products, norm_key):
                continue
            column = getattr(Products, norm_key)

            if isinstance(value, str):
                query = query.where(column.ilike(f"%{value}%"))
            else:
                query = query.where(column == value)

        return query

    @staticmethod
    def _normalize_filter_key(key: str) -> str:
        """
        Normalize filter key to match database column name.

        Args:
            key: Filter key

        Returns:
            str: Normalized column name
        """
        key_mapping = {
            "id": "xml_id",
            "xml_id": "xml_id",
            "name": "name",
            "category": "product_category",
            "product_category": "product_category",
            "productcategory": "product_category",
            "certificate": "documents_from_factory",
            "cert": "documents_from_factory",
            "min_price": "min_price",
            "max_price": "max_price",
        }
        return key_mapping.get(key.lower(), key.lower())

    @staticmethod
    def resolve_params(params) -> tuple[int, int]:
        """
        Resolve pagination parameters.

        Args:
            params: Pagination parameters object with page and size attributes

        Returns:
            tuple[int, int]: Offset and size tuple
        """
        page = max(1, params.page or 1)
        size = params.size or 20
        size = min(size, 100)
        offset = (page - 1) * size
        return offset, size

    @staticmethod
    def parse_filter(
        name: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        certificate: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Build filters dict from explicit query params.

        Args:
            name: Filter by product name
            min_price: Minimum price filter
            max_price: Maximum price filter
            certificate: Filter by certificate
            category: Filter by category

        Returns:
            Optional[Dict[str, Any]]: Filters dictionary or None if no filters
        """
        filters: Dict[str, Any] = {}

        if name:
            filters["name"] = name
        if category:
            filters["category"] = category
        if certificate:
            filters["certificate"] = certificate
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price

        return filters if filters else None


class CategoryRepository:
    """Repository class for Category database operations."""

    @staticmethod
    async def fetch_category_by_id(db: AsyncSession, category_id: str) -> Optional[Categories]:
        """
        Fetch a category by ID (accepts integer as string).

        Args:
            db: Database session
            category_id: Category ID as string

        Returns:
            Optional[Categories]: Category if found, None otherwise
        """
        try:
            category_id_int = int(category_id)
            result = await db.execute(
                select(Categories).where(
                    and_(Categories.id == category_id_int, Categories.deleted_at.is_(None))
                )
            )
            return result.scalar_one_or_none()
        except (ValueError, TypeError):
            return None

    @staticmethod
    async def fetch_category_by_uuid(db: AsyncSession, uuid: str) -> Optional[Categories]:
        """
        Fetch a category by UUID (deprecated, use fetch_category_by_id).

        UUID column removed - tries to parse as ID instead.

        Args:
            db: Database session
            uuid: UUID string (will be parsed as integer ID)

        Returns:
            Optional[Categories]: Category if found, None otherwise
        """
        try:
            category_id_int = int(uuid)
            result = await db.execute(
                select(Categories).where(
                    and_(Categories.id == category_id_int, Categories.deleted_at.is_(None))
                )
            )
            return result.scalar_one_or_none()
        except (ValueError, TypeError):
            return None

    @staticmethod
    async def get_category_references_by_bitrix_id(
        db: AsyncSession, bitrix_id: int
    ) -> Dict[str, Optional[str]]:
        """
        Get category_uuid, parent_category_uuid and sub_category_uuid for a product based on section_id (bitrix_id).

        This method fetches the category by bitrix_id and returns:
        - category_uuid: The UUID of the category matching the bitrix_id
        - parent_category_uuid: Root parent UUID (from category record)
        - sub_category_uuid: Direct parent UUID (from category record, for level 3+)

        Args:
            db: Database session
            bitrix_id: Bitrix category ID (section_id from product)

        Returns:
            Dict with category_uuid, parent_category_uuid and sub_category_uuid
        """
        if not bitrix_id:
            return {
                "category_uuid": None,
                "parent_category_uuid": None,
                "sub_category_uuid": None,
            }

        # Find category by bitrix_id
        result = await db.execute(
            select(Categories).where(
                and_(Categories.bitrix_id == bitrix_id, Categories.deleted_at.is_(None))
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            return {
                "category_uuid": None,
                "parent_category_uuid": None,
                "sub_category_uuid": None,
            }

        # Return category ID and its stored hierarchy fields (using uuid field names for backward compatibility)
        return {
            "category_uuid": str(category.id),
            "parent_category_uuid": (
                str(category.parent_category_id) if category.parent_category_id else None
            ),
            "sub_category_uuid": (
                str(category.sub_category_id) if category.sub_category_id else None
            ),
        }


class ProductListDatabaseHelper:
    """
    Helper class for product list database operations.

    Provides methods for fetching paginated product lists with filters,
    sorting, and category name resolution via joins.
    Gets primary supplier name from ProductSupplierMapping bridge table.
    """

    _base_url: Optional[str] = None

    @classmethod
    def _get_base_url(cls) -> str:
        """Get cached base URL for blob storage."""
        if cls._base_url is None:
            settings = get_settings()
            base_url = settings.AZURE_BLOB_STORAGE_URL or ""
            cls._base_url = base_url.rstrip("/") if base_url else ""
        return cls._base_url

    @staticmethod
    def _extract_and_build_url(path: Optional[str], url: Optional[str]) -> Optional[str]:
        """
        Extract URL from document and build full URL.

        Extracts from path JSON (downloadUrl/showUrl) or uses url field,
        then prepends base URL if relative.

        Args:
            path: Path JSON string or path string
            url: Direct URL field

        Returns:
            Optional[str]: Full image URL or None
        """
        # Extract relative path from path JSON or use path/url directly
        relative_path = None
        if path:
            try:
                path_data = json.loads(path) if isinstance(path, str) else path
                if isinstance(path_data, dict):
                    relative_path = path_data.get("downloadUrl") or path_data.get("showUrl")
            except (json.JSONDecodeError, TypeError):
                relative_path = path
        elif url:
            relative_path = url

        if not relative_path:
            return None

        # Build full URL
        if relative_path.startswith(("http://", "https://")):
            return relative_path

        base_url = ProductListDatabaseHelper._get_base_url()
        return f"{base_url}{relative_path}" if base_url else relative_path

    @staticmethod

    async def _fetch_factory_logo_urls(
        db: AsyncSession, product_ids: List[int]
    ) -> Dict[int, str]:
        """
        Fetch factory_logo image URLs for multiple products in batch.

        Args:
            db: Database session
            product_ids: List of product IDs

        Returns:
            Dict[int, str]: Mapping of product_id to image_url (empty string if not found)
        """
        if not product_ids:
            return {}

        result = await db.execute(
            select(Documents.path, Documents.url, Documents.mapping_id)
            .where(
                and_(
                    Documents.source_table == "products",
                    Documents.mapping_id.in_(product_ids),
                    Documents.deleted_at.is_(None),
                    or_(
                        Documents.doc_type == "factory_logo",
                        Documents.path.like("%/factory_logo/%"),
                        Documents.url.like("%/factory_logo/%"),
                    ),
                )
            )
            .distinct()
        )

        # Build mapping using dict comprehension with first match per product
        url_map: Dict[int, str] = {}
        for path, url, mapping_id in result.all():
            if mapping_id and mapping_id not in url_map:
                image_url = ProductListDatabaseHelper._extract_and_build_url(path, url)
                if image_url:
                    url_map[mapping_id] = image_url

        return url_map

    @staticmethod
    async def fetch_product_list(
        db: AsyncSession,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        sub_category_id: Optional[str] = None,
        child_category_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[ProductListItem], int]:
        """
        Fetch product list with filters, sorting, and pagination.

        Uses relationships to load category and supplier data via selectinload.

        Args:
            db: Database session
            page: Page number (default 1)
            limit: Items per page (default 10)
            search: Search by id or name
            category_id: Filter by category id
            sub_category_id: Filter by sub category id
            child_category_id: Filter by child category id
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            sort_by: Sort field (created_at, updated_at)
            sort_order: Sort order (asc, desc)

        Returns:
            Tuple[List[ProductListItem], int]: Product list items and total count
        """
        # Base query with relationships using selectinload
        query = (
            select(Products)
            .options(
                selectinload(Products.category),
                selectinload(Products.parent_category),
                selectinload(Products.sub_category),
                selectinload(Products.product_suppliers).selectinload(
                    ProductSupplierMapping.supplier
                ),
            )
            .filter(Products.parent_product_id.is_(None))
            .filter(Products.deleted_at.is_(None))
        )

        # Search filter (by id or name)
        if search:
            search_conditions = [Products.name.ilike(f"%{search}%")]
            if search.isdigit():
                search_conditions.append(Products.id == int(search))
            search_filter = or_(*search_conditions)
            query = query.where(search_filter)

        # Category filters - prioritize most specific filter
        # Logic: If child_category_id is provided, use only that (most specific)
        #        Otherwise, if sub_category_id is provided, use that
        #        Otherwise, use category_id
        #        When multiple filters provided, ensure hierarchy consistency
        
        if child_category_id:
            # Level 3 - most specific: filter by category_id only
            try:
                child_category_id_int = int(child_category_id)
                query = query.where(Products.category_id == child_category_id_int)
                
                # If parent filters are also provided, ensure hierarchy consistency
                if sub_category_id:
                    try:
                        sub_category_id_int = int(sub_category_id)
                        query = query.where(Products.sub_category_id == sub_category_id_int)
                    except ValueError:
                        pass
                
                if category_id:
                    try:
                        category_id_int = int(category_id)
                        query = query.where(Products.parent_category_id == category_id_int)
                    except ValueError:
                        pass
            except ValueError:
                pass
        
        elif sub_category_id:
            # Level 2 - filter by category_id OR sub_category_id
            try:
                sub_category_id_int = int(sub_category_id)
                query = query.where(
                    or_(
                        Products.category_id == sub_category_id_int,
                        Products.sub_category_id == sub_category_id_int,
                    )
                )
                
                # If category_id is also provided, ensure hierarchy consistency
                if category_id:
                    try:
                        category_id_int = int(category_id)
                        query = query.where(Products.parent_category_id == category_id_int)
                    except ValueError:
                        pass
            except ValueError:
                pass
        
        elif category_id:
            # Level 1 - filter by parent_category_id OR category_id
            try:
                category_id_int = int(category_id)
                query = query.where(
                    or_(
                        Products.parent_category_id == category_id_int,
                        Products.category_id == category_id_int,
                    )
                )
            except ValueError:
                pass

        # Date range filter
        if start_date or end_date:
            if start_date and end_date:
                # Both dates provided - filter between dates
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                date_filter = Products.created_at.between(start_datetime, end_datetime)
                query = query.where(date_filter)
            elif start_date:
                # Only start date - filter from start date onwards
                start_datetime = datetime.combine(start_date, datetime.min.time())
                query = query.where(Products.created_at >= start_datetime)
            elif end_date:
                # Only end date - filter up to end date
                end_datetime = datetime.combine(end_date, datetime.max.time())
                query = query.where(Products.created_at <= end_datetime)

        # Group by product to handle multiple supplier mappings (get first supplier)
        query = query.group_by(
            Products.id,
            Products.category_type,
        )

        # Sorting (safe whitelist)
        sort_column_map = {
            "created_at": Products.created_at,
            "updated_at": Products.updated_at,
        }
        sort_column = sort_column_map.get(sort_by, Products.created_at)

        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Get total count get count using query
        total = await db.scalar(select(func.count()).select_from(query)) or 0

        # Pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()

        # Fetch factory_logo URLs for all products in batch
        product_ids = [product.id for product in products]
        image_url_map = await ProductListDatabaseHelper._fetch_factory_logo_urls(db, product_ids)

        # Build product list items using relationships
        for product in products:
            # Get category names from relationships
            category_name = product.category.name if product.category else None
            parent_category_name = product.parent_category.name if product.parent_category else None
            sub_category_name = product.sub_category.name if product.sub_category else None

            # Get primary supplier name from product_suppliers relationship
            primary_supplier_name = None
            if product.product_suppliers:
                # Get first supplier (primary supplier)
                for mapping in product.product_suppliers:
                    if mapping.supplier:
                        primary_supplier_name = mapping.supplier.company_name
                        break
            # add all data into a product no need item
            product.category_name = category_name
            product.parent_category_name = parent_category_name
            product.sub_category_name = sub_category_name
            product.primary_supplier_name = primary_supplier_name
            product.category_type = product.category_type
            product.image_url = image_url_map.get(product.id) or ""

        return products, total


class CategoryListDatabaseHelper:
    """
    Database helper for product category listing with 3-level hierarchy
    and optimized product counts.

    Hierarchy Structure (using parent_category_id and sub_category_id):
        Level 1 (Root): parent_category_id IS NULL
        Level 2 (Sub-category): parent_category_id = Level1.id AND sub_category_id IS NULL
        Level 3 (Child): sub_category_id = Level2.id

    Search searches across all levels and returns matching items with their hierarchy.
    """

    @staticmethod
    async def fetch_category_list(
        db: AsyncSession,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Fetch category list with 3-level hierarchy and product counts.

        Single query approach with maximum 2 loops:
        - Fetch ALL categories in ONE query
        - Loop 1: Categorize into level1_by_id, level2_by_id, level3_by_id
        - Loop 2: Build hierarchy tree structure

        Uses two columns for hierarchy:
            - parent_category_id: Links Level 2 to Level 1
            - sub_category_id: Links Level 3 to Level 2

        Categorization logic:
            - Level 1: parent_category_id IS NULL AND sub_category_id IS NULL
            - Level 2: parent_category_id IS NOT NULL AND sub_category_id IS NULL
            - Level 3: parent_category_id IS NOT NULL AND sub_category_id IS NOT NULL

        Search works across all levels:
            - If Level 1 matches, includes all its descendants
            - If Level 2 matches, includes its Level 1 parent and Level 3 children
            - If Level 3 matches, includes its Level 2 and Level 1 parents

        Args:
            db: Async database session
            search: Search by category name across all levels (case-insensitive)
            sort_by: created_at | updated_at
            sort_order: asc | desc

        Returns:
            Tuple[List[Dict], int]: category items with nested children, total product count
        """
        # Sorting configuration
        sort_column_map = {
            "created_at": Categories.created_at,
            "updated_at": Categories.updated_at,
        }
        sort_column = sort_column_map.get(sort_by, Categories.created_at)
        order_func = sort_column.asc() if sort_order.lower() == "asc" else sort_column.desc()

        # ---------------------------
        # SINGLE QUERY: Fetch ALL categories
        # ---------------------------
        all_categories_query = select(Categories).where(Categories.deleted_at.is_(None)).order_by(order_func)
        result = await db.execute(all_categories_query)
        all_categories = result.scalars().all()

        if not all_categories:
            return [], 0

        # ---------------------------
        # Product count query
        # ---------------------------
        product_count_query = (
            select(
                Products.category_id,
                func.count(Products.id).label("product_count"),
            )
            .filter(Products.parent_product_id.is_(None))
            .filter(Products.deleted_at.is_(None))
            .group_by(Products.category_id)
        )
        count_result = await db.execute(product_count_query)
        product_count_map = {row.category_id: row.product_count for row in count_result.all()}
        all_product_count = sum(product_count_map.values())

        # ---------------------------
        # SINGLE LOOP: Categorize all categories and build all item dictionaries
        # ---------------------------
        level1_by_id: Dict[int, Categories] = {}
        level2_by_id: Dict[int, Categories] = {}
        level3_by_id: Dict[int, Categories] = {}

        # Relationship maps for building hierarchy
        level2_to_level1: Dict[int, int] = {}  # level2_id -> level1_id
        level3_to_level2: Dict[int, int] = {}  # level3_id -> level2_id
        level1_children: Dict[int, List[int]] = {}  # level1_id -> [level2_ids]
        level2_children: Dict[int, List[int]] = {}  # level2_id -> [level3_ids]

        # Item dictionaries for building hierarchy - build all in one loop
        level1_items: Dict[int, Dict[str, Any]] = {}
        level2_items: Dict[int, Dict[str, Any]] = {}
        level3_items: Dict[int, Dict[str, Any]] = {}

        # Search tracking
        search_pattern = search.lower() if search else None
        matched_level1_ids: Set[int] = set()
        matched_level2_ids: Set[int] = set()
        matched_level3_ids: Set[int] = set()

        for cat in all_categories:
            # Categorize based on parent_category_id and sub_category_id
            is_level1 = cat.parent_category_id is None and cat.sub_category_id is None
            is_level2 = cat.parent_category_id is not None and cat.sub_category_id is None
            is_level3 = cat.parent_category_id is not None and cat.sub_category_id is not None

            # Build item dictionary for all levels in one loop
            item_dict = {
                "id": str(cat.id),
                "name": cat.name or "",
                "description": cat.code or "",
                "status": "active" if cat.deleted_at is None else "inactive",
                "product_count": product_count_map.get(cat.id, 0),
                "parent_id": (str(cat.parent_category_id) if cat.parent_category_id else None),
                "subcategory_id": (str(cat.sub_category_id) if cat.sub_category_id else None),
                "child_categories": [],
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
            }

            if is_level1:
                level1_by_id[cat.id] = cat
                level1_items[cat.id] = item_dict
                if search_pattern and cat.name and search_pattern in cat.name.lower():
                    matched_level1_ids.add(cat.id)
            elif is_level2:
                level2_by_id[cat.id] = cat
                level2_to_level1[cat.id] = cat.parent_category_id
                level1_children.setdefault(cat.parent_category_id, []).append(cat.id)
                level2_items[cat.id] = item_dict
                if search_pattern and cat.name and search_pattern in cat.name.lower():
                    matched_level2_ids.add(cat.id)
            elif is_level3:
                level3_by_id[cat.id] = cat
                level3_to_level2[cat.id] = cat.sub_category_id
                level2_children.setdefault(cat.sub_category_id, []).append(cat.id)
                level3_items[cat.id] = item_dict
                if search_pattern and cat.name and search_pattern in cat.name.lower():
                    matched_level3_ids.add(cat.id)

        # ---------------------------
        # Apply search filter (expand matches to include ancestors/descendants)
        # ---------------------------
        if search_pattern:
            # Expand descendants
            level2_from_l1 = {
                l2_id for l1_id in matched_level1_ids for l2_id in level1_children.get(l1_id, [])
            }
            expanded_level2_ids = matched_level2_ids | level2_from_l1
            level3_from_l2 = {
                l3_id for l2_id in expanded_level2_ids for l3_id in level2_children.get(l2_id, [])
            }

            # Expand ancestors
            level2_parent_ids = {
                level2_to_level1[l2_id] for l2_id in matched_level2_ids if l2_id in level2_to_level1
            }
            level3_l2_parent_ids = {
                level3_to_level2[l3_id] for l3_id in matched_level3_ids if l3_id in level3_to_level2
            }
            level3_l1_grandparent_ids = {
                level2_to_level1[l2_id]
                for l2_id in level3_l2_parent_ids
                if l2_id in level2_to_level1
            }

            required_level1_ids = matched_level1_ids | level2_parent_ids | level3_l1_grandparent_ids
            required_level2_ids = matched_level2_ids | level2_from_l1 | level3_l2_parent_ids
            required_level3_ids = matched_level3_ids | level3_from_l2

            if not required_level1_ids and not required_level2_ids and not required_level3_ids:
                return [], all_product_count
        else:
            required_level1_ids = set(level1_by_id.keys())
            required_level2_ids = set(level2_by_id.keys())
            required_level3_ids = set(level3_by_id.keys())

        # Filter items to only include required ones and attach children in one pass
        level3_items = {k: v for k, v in level3_items.items() if k in required_level3_ids}

        # Build Level 2 items with children attached (no separate loop)
        level2_items = {
            l2_id: {
                **item,
                "child_categories": [
                    level3_items[l3_id]
                    for l3_id in level2_children.get(l2_id, [])
                    if l3_id in level3_items
                ],
                "subcategory_id": None,
            }
            for l2_id, item in level2_items.items()
            if l2_id in required_level2_ids
        }
        # Update product_count for level2 items
        level2_items = {
            l2_id: {
                **item,
                "product_count": item["product_count"]
                + sum(child["product_count"] for child in item["child_categories"]),
            }
            for l2_id, item in level2_items.items()
        }

        # Build Level 1 items with children attached (no separate loop)
        level1_items = {
            l1_id: {
                **item,
                "child_categories": [
                    level2_items[l2_id]
                    for l2_id in level1_children.get(l1_id, [])
                    if l2_id in level2_items
                ],
                "parent_id": None,
                "subcategory_id": None,
            }
            for l1_id, item in level1_items.items()
            if l1_id in required_level1_ids
        }
        # Update product_count for level1 items
        level1_items = {
            l1_id: {
                **item,
                "product_count": item["product_count"]
                + sum(child["product_count"] for child in item["child_categories"]),
            }
            for l1_id, item in level1_items.items()
        }

        # Convert level1_items to list
        items = list(level1_items.values())

        return items, all_product_count


class GetProductDetailsDatabaseHelper:
    """
    Database helper class for Product Detail API.

    This class contains ONLY database queries.
    No business logic should live here.
    """

    ## query product by id full object
    @staticmethod
    async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Products]:
        """
        Fetch a product by its unique identifier.

        Args:
            db: Database session
            product_id: Product ID

        Returns:
            Optional[Products]: Product if found, None otherwise
        """
        result = await db.execute(
            select(Products).where(
                and_(Products.id == product_id, Products.deleted_at.is_(None))
            )
        )
        return result.scalar_one_or_none()

    ## Query supplier from suppplier table using the product_supplier_mapping table
    @staticmethod
    async def get_supplier_by_product_id(db: AsyncSession, product_id: int) -> List[Suppliers]:
        """
        Fetch suppliers associated with a product via ProductSupplierMapping.

        Args:
            db: Database session
            product_id: Product ID

        Returns:
            List[Suppliers]: List of suppliers associated with the product
        """
        result = await db.execute(
            select(Suppliers)
            .join(ProductSupplierMapping)
            .where(ProductSupplierMapping.product_id == product_id)
        )
        return list(result.scalars().all())

    ## Query logistics from logistic table using the where logistic.product_id == product_id
    @staticmethod
    async def get_logistics_by_product_id(db: AsyncSession, product_id: int) -> Optional[Logistic]:
        """
        Fetch logistics information for a product.

        Args:
            db: Database session
            product_id: Product ID

        Returns:
            Optional[Logistic]: Logistics information if found, None otherwise
        """
        result = await db.execute(select(Logistic).where(Logistic.product_id == product_id))
        return result.scalar_one_or_none()

    ## Query documents from documents table where mapping_table == 'products' and mapping_id == product_id
    @staticmethod
    async def get_documents_by_product_id(db: AsyncSession, product_id: int) -> List[Documents]:
        """
        Fetch documents associated with a product.

        Args:
            db: Database session
            product_id: Product ID

        Returns:
            List[Documents]: List of documents associated with the product
        """
        result = await db.execute(
            select(Documents).where(
                Documents.source_table == "products", Documents.mapping_id == product_id
            )
        )
        return list(result.scalars().all())

    @staticmethod
    def _extract_url_from_document(document: Documents) -> Optional[str]:
        """
        Extract URL from document and prepend base URL if needed.

        Extracts URL from path JSON (prefers downloadUrl, then showUrl) or falls back to url field.
        Prepends AZURE_BLOB_STORAGE_URL if the extracted path is relative.

        Args:
            document: Documents model instance

        Returns:
            Optional[str]: Full image URL or None
        """
        if not document:
            return None

        settings = get_settings()
        base_url = settings.AZURE_BLOB_STORAGE_URL or ""

        # Try to extract URL from path JSON (Bitrix URLs)
        if document.path:
            try:
                path_data = json.loads(document.path) if isinstance(document.path, str) else document.path
                if isinstance(path_data, dict):
                    # Prefer downloadUrl, fallback to showUrl
                    relative_path = path_data.get("downloadUrl") or path_data.get("showUrl")
                    if relative_path:
                        # If path is relative, prepend base URL
                        if base_url and not relative_path.startswith(("http://", "https://")):
                            base_url = base_url.rstrip("/")
                            return f"{base_url}{relative_path}" if base_url else relative_path
                        return relative_path
            except (json.JSONDecodeError, TypeError):
                pass

        # Fallback to url field (Azure blob storage URL)
        if document.url:
            return document.url

        return None

    @staticmethod
    async def get_factory_logo_url(db: AsyncSession, product_id: int) -> Optional[str]:
        """
        Fetch factory logo image URL from documents table.

        Looks for document where:
        - source_table == 'products'
        - doc_type == 'factory_logo'
        - mapping_id == product_id

        Extracts URL from path JSON (prefers downloadUrl, then showUrl) or falls back to url field.

        Args:
            db: Database session
            product_id: Product ID

        Returns:
            Optional[str]: Factory logo URL if found, None otherwise
        """
        result = await db.execute(
            select(Documents).where(
                Documents.source_table == "products",
                Documents.doc_type == "factory_logo",
                Documents.mapping_id == product_id,
            )
        )
        document = result.scalar_one_or_none()
        return GetProductDetailsDatabaseHelper._extract_url_from_document(document)

    @staticmethod
    async def get_factory_logo_urls_batch(
        db: AsyncSession, product_ids: List[int]
    ) -> Dict[int, Optional[str]]:
        """
        Fetch factory logo image URLs for multiple products in a single query.

        Args:
            db: Database session
            product_ids: List of product IDs

        Returns:
            Dict[int, Optional[str]]: Mapping of product_id to factory_logo_url
        """
        if not product_ids:
            return {}

        result = await db.execute(
            select(Documents).where(
                Documents.source_table == "products",
                Documents.doc_type == "factory_logo",
                Documents.mapping_id.in_(product_ids),
            )
        )
        documents = result.scalars().all()

        # Build mapping of product_id to URL
        url_map: Dict[int, Optional[str]] = {}
        for document in documents:
            url = GetProductDetailsDatabaseHelper._extract_url_from_document(document)
            url_map[document.mapping_id] = url

        # Set None for products without factory_logo
        for product_id in product_ids:
            if product_id not in url_map:
                url_map[product_id] = None

        return url_map

    ## method which take all the above queries and return the product details
    @staticmethod
    async def get_product_details(db: AsyncSession, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch complete product details including product, suppliers, logistics, and documents.
        Also fetches category names for category, parent_category, and sub_category.

        Args:
            db: Database session
            product_id: Product ID

        Returns:
            Optional[Dict[str, Any]]: Dictionary with product, supplier, logistics, and documents
                if product found, None otherwise
        """
        # Aliases for category joins
        Category = aliased(Categories)
        ParentCategory = aliased(Categories)
        SubCategory = aliased(Categories)
        # Query product with category name joins
        query = (
            select(
                Products,
                Category.name.label("category_name"),
                ParentCategory.name.label("parent_category_name"),
                SubCategory.name.label("sub_category_name"),
            )
            .options(
                selectinload(Products.updated_by_user), selectinload(Products.generated_by_user)
            )
            .outerjoin(Category, Products.category_id == Category.id)
            .outerjoin(ParentCategory, Products.parent_category_id == ParentCategory.id)
            .outerjoin(SubCategory, Products.sub_category_id == SubCategory.id)
            .where(and_(Products.id == product_id, Products.deleted_at.is_(None)))
        )

        result = await db.execute(query)
        row = result.first()

        if not row:
            return None

        product = row[0]
        category_name = row[1] or ""
        parent_category_name = row[2] or ""
        sub_category_name = row[3] or ""

        # Attach category names to product object
        setattr(product, "category_name", category_name)
        setattr(product, "parent_category_name", parent_category_name)
        setattr(product, "sub_category_name", sub_category_name)

        # Load user relationships and set names for serializer
        updated_by = product.updated_by_user.name if product.updated_by_user else None
        generated_by = product.generated_by_user.name if product.generated_by_user else None

        supplier = await GetProductDetailsDatabaseHelper.get_supplier_by_product_id(db, product_id)
        logistics = await GetProductDetailsDatabaseHelper.get_logistics_by_product_id(
            db, product_id
        )
        documents = await GetProductDetailsDatabaseHelper.get_documents_by_product_id(
            db, product_id
        )
        factory_logo_url = await GetProductDetailsDatabaseHelper.get_factory_logo_url(
            db, product_id
        )

        return {
            "product": product,
            "supplier": supplier,
            "logistics": logistics,
            "documents": documents,
            "updated_by": updated_by,
            "generated_by": generated_by,
            "factory_logo_url": factory_logo_url,
        }
