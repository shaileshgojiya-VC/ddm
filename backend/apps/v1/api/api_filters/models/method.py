"""
Inquiry and Supplier Filter Database Methods
Pure DB access layer
"""

from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.customer.models.model import Customers
from apps.v1.api.request.models.model import Requests, Stage
from apps.v1.api.auth.models.model import Users
from apps.v1.api.products.models.model import Products, Categories
from apps.v1.api.suppliers.models.model import Suppliers


class InquiryFilterDatabaseMethods:
    """
    Database helper for inquiry dynamic filter metadata
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------
    # Get All Filters (Combined)
    # ---------------------------------------------------------
    async def get_all_filters(self) -> Dict[str, Any]:
        """
        Fetch all inquiry filter metadata in a single method.

        Returns:
            Dict containing stages (grouped by phase), assignees, countries,
            customers, products, and date range.
        """
        # --------------------------------------------------
        # STAGES (ordered & grouped by phase)
        # --------------------------------------------------
        stages_query = (
            select(
                Stage.id.label("value"),
                Stage.stage_name.label("label"),
                Stage.phase,
                Stage.order_sequence,
            )
            .where(Stage.stage_name.isnot(None))
            .where(Stage.stage_name != "")
            .order_by(Stage.phase, Stage.order_sequence)
        )

        stages_result = await self.db.execute(stages_query)

        grouped_stages: Dict[str, List[Dict[str, Any]]] = {}

        for value, label, phase, order_sequence in stages_result.all():
            phase_key = (
                phase.name.upper()
                if hasattr(phase, "name")
                else str(phase).upper()
            )

            grouped_stages.setdefault(phase_key, []).append(
                {
                    "label": label,
                    "value": value,
                    "order_sequence": order_sequence or 0,
                }
            )

        # --------------------------------------------------
        # ASSIGNEES
        # --------------------------------------------------
        assignees_query = (
            select(Users.id, Users.name)
            .where(Users.name.isnot(None))
            .distinct()
            .order_by(Users.name)
        )

        assignees_result = await self.db.execute(assignees_query)

        assignees = [
            {"label": name, "value": user_id}
            for user_id, name in assignees_result.all()
        ]

        # --------------------------------------------------
        # COUNTRIES
        # --------------------------------------------------
        countries_query = (
            select(Requests.country)
            .where(Requests.country.isnot(None))
            .where(Requests.deleted_at.is_(None))
            .distinct()
            .order_by(Requests.country)
        )

        countries_result = await self.db.execute(countries_query)

        countries = [
            {"label": country, "value": country}
            for (country,) in countries_result.all()
        ]

        # --------------------------------------------------
        # CUSTOMERS
        # --------------------------------------------------
        customers_query = (
            select(Customers.id, Customers.company_name)
            .where(Customers.company_name.isnot(None))
            .where(Customers.deleted_at.is_(None))
            .distinct()
            .order_by(Customers.company_name)
        )

        customers_result = await self.db.execute(customers_query)

        customers = [
            {"label": name, "value": customer_id}
            for customer_id, name in customers_result.all()
        ]

        # --------------------------------------------------
        # PRODUCTS
        # --------------------------------------------------
        products_query = (
            select(Products.id, Products.name)
            .where(Products.name.isnot(None))
            .where(Products.deleted_at.is_(None))
            .distinct()
            .order_by(Products.name)
        )

        products_result = await self.db.execute(products_query)

        products = [
            {"label": name, "value": product_id}
            for product_id, name in products_result.all()
        ]

        # --------------------------------------------------
        # DATE RANGE
        # --------------------------------------------------
        date_range_query = select(
            func.min(Requests.created_at),
            func.max(Requests.created_at),
        ).where(Requests.deleted_at.is_(None))

        date_result = await self.db.execute(date_range_query)
        min_date, max_date = date_result.one()

        # --------------------------------------------------
        # FINAL RESPONSE
        # --------------------------------------------------
        return {
            "stages": grouped_stages,  # LEAD / REGISTRATION / DEAL
            "assignees": assignees,
            "countries": countries,
            "customers": customers,
            "products": products,
            "date_range": {
                "min_date": min_date.isoformat() if min_date else None,
                "max_date": max_date.isoformat() if max_date else None,
            },
        }


class SupplierFilterDatabaseMethods:
    """
    Database helper for supplier dynamic filter metadata
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------
    # Countries (for Suppliers)
    # ---------------------------------------------------------
    async def get_distinct_countries(self) -> List[Dict[str, str]]:
        query = (
            select(Suppliers.country)
            .where(Suppliers.country.isnot(None))
            .where(Suppliers.country != "")
            .where(Suppliers.deleted_at.is_(None))
            .distinct()
        )

        result = await self.db.execute(query)

        return [{"label": country, "value": country} for (country,) in result.all()]

    # ---------------------------------------------------------
    # Categories (Level 1 - Root categories)
    # ---------------------------------------------------------
    async def get_distinct_categories(self) -> List[Dict[str, str]]:
        query = (
            select(Categories.id, Categories.name)
            .where(Categories.name.isnot(None))
            .where(Categories.name != "")
            .where(Categories.parent_category_id.is_(None))
            .where(Categories.deleted_at.is_(None))
            .distinct()
            .order_by(Categories.name)
        )

        result = await self.db.execute(query)

        return [{"label": name, "value": cat_id} for cat_id, name in result.all()]

    # ---------------------------------------------------------
    # Sub Categories (Level 2 - Has parent but no sub_category)
    # ---------------------------------------------------------
    async def get_distinct_sub_categories(self) -> List[Dict[str, str]]:
        query = (
            select(Categories.id, Categories.name)
            .where(Categories.name.isnot(None))
            .where(Categories.name != "")
            .where(Categories.parent_category_id.isnot(None))
            .where(Categories.sub_category_id.is_(None))
            .where(Categories.deleted_at.is_(None))
            .distinct()
            .order_by(Categories.name)
        )

        result = await self.db.execute(query)

        return [{"label": name, "value": cat_id} for cat_id, name in result.all()]

    # ---------------------------------------------------------
    # Child Categories (Level 3 - Has sub_category_id)
    # ---------------------------------------------------------
    async def get_distinct_child_categories(self) -> List[Dict[str, str]]:
        query = (
            select(Categories.id, Categories.name)
            .where(Categories.name.isnot(None))
            .where(Categories.name != "")
            .where(Categories.sub_category_id.isnot(None))
            .where(Categories.deleted_at.is_(None))
            .distinct()
            .order_by(Categories.name)
        )

        result = await self.db.execute(query)

        return [{"label": name, "value": cat_id} for cat_id, name in result.all()]

    # ---------------------------------------------------------
    # Date Range (for Suppliers)
    # ---------------------------------------------------------
    async def get_date_range(self) -> Dict[str, str]:
        query = select(
            func.min(Suppliers.created_at),
            func.max(Suppliers.created_at),
        ).where(Suppliers.deleted_at.is_(None))

        result = await self.db.execute(query)
        min_date, max_date = result.one()

        return {
            "min_date": min_date.isoformat() if min_date else None,
            "max_date": max_date.isoformat() if max_date else None,
        }


class ProductFilterDatabaseMethods:
    """
    Database helper for product dynamic filter metadata
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------
    # Categories (Level 1 - Root categories)
    # ---------------------------------------------------------
    async def get_distinct_categories(self) -> List[Dict[str, str]]:
        query = (
            select(Categories.id, Categories.name)
            .where(Categories.name.isnot(None))
            .where(Categories.name != "")
            .where(Categories.parent_category_id.is_(None))
            .where(Categories.deleted_at.is_(None))
            .distinct()
            .order_by(Categories.name)
        )

        result = await self.db.execute(query)

        return [{"label": name, "value": cat_id} for cat_id, name in result.all()]

    # ---------------------------------------------------------
    # Sub Categories (Level 2 - Has parent but no sub_category)
    # ---------------------------------------------------------
    async def get_distinct_sub_categories(self) -> List[Dict[str, str]]:
        query = (
            select(Categories.id, Categories.name)
            .where(Categories.name.isnot(None))
            .where(Categories.name != "")
            .where(Categories.parent_category_id.isnot(None))
            .where(Categories.sub_category_id.is_(None))
            .where(Categories.deleted_at.is_(None))
            .distinct()
            .order_by(Categories.name)
        )

        result = await self.db.execute(query)

        return [{"label": name, "value": cat_id} for cat_id, name in result.all()]

    # ---------------------------------------------------------
    # Child Categories (Level 3 - Has sub_category_id)
    # ---------------------------------------------------------
    async def get_distinct_child_categories(self) -> List[Dict[str, str]]:
        query = (
            select(Categories.id, Categories.name)
            .where(Categories.name.isnot(None))
            .where(Categories.name != "")
            .where(Categories.sub_category_id.isnot(None))
            .where(Categories.deleted_at.is_(None))
            .distinct()
            .order_by(Categories.name)
        )

        result = await self.db.execute(query)

        return [{"label": name, "value": cat_id} for cat_id, name in result.all()]


class UserFilterDatabaseMethods:
    """
    Database helper for user dynamic filter metadata
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # User filters only have static role filter, no dynamic filters needed


class DashboardFilterDatabaseMethods:
    """
    Database helper for dashboard dynamic filter metadata
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------
    # Date Range (for Dashboard - from Requests)
    # ---------------------------------------------------------
    async def get_date_range(self) -> Dict[str, str]:
        query = select(
            func.min(Requests.created_at),
            func.max(Requests.created_at),
        ).where(Requests.deleted_at.is_(None))

        result = await self.db.execute(query)
        min_date, max_date = result.one()

        return {
            "min_date": min_date.isoformat() if min_date else None,
            "max_date": max_date.isoformat() if max_date else None,
        }
