"""
Centralized Filter Registry

This file defines:
- Filter types
- Static filter options
- Module-wise filter configurations
- A single registry mapping modules to filters

Used by:
GET /v1/filters?module=<module-name>
"""

# -------------------------------------------------------------------
# Filter Types
# -------------------------------------------------------------------

FILTER_TYPES = {
    "STATIC": "static",  # Fixed enum values
    "DYNAMIC": "dynamic",  # DB-driven distinct values
    "SEARCH": "search",  # Text input
    "DATE_RANGE": "date_range",  # Date range picker
    "MULTI_SEARCH": "multi_search",
}


# -------------------------------------------------------------------
# Static Options (Enums)
# -------------------------------------------------------------------

STATIC_OPTIONS = {
    "priority": [
        {"label": "All", "value": "all"},
        {"label": "Urgent", "value": "urgent"},
        {"label": "High", "value": "high"},
        {"label": "Medium", "value": "medium"},
        {"label": "Low", "value": "low"},
    ],
    "status": [
        {"label": "All Status", "value": "all"},
        {"label": "Pending Response", "value": "pending_response"},
        {"label": "Awaiting Client", "value": "awaiting_client"},
        {"label": "Follow-up Required", "value": "followed_up_required"},
        {"label": "Delayed", "value": "delayed"},
        {"label": "On Track", "value": "on_track"},
    ],
    "phase": [
        {"label": "All", "value": "all"},
        {"label": "Leads", "value": "lead"},
        {"label": "Registration", "value": "registration"},
        {"label": "Deals", "value": "deal"},
    ],
    "roles": [
        {"label": "All Roles", "value": "all"},
        {"label": "Admin", "value": "admin"},
        {"label": "Management", "value": "management"},
        {"label": "Sales", "value": "sales"},
    ],
    "company_type": [
        {"label": "Manufacturer", "value": "manufacturer"},
        {"label": "Distributor", "value": "distributor"},
        {"label": "Retailer", "value": "retailer"},
        {"label": "Other", "value": "other"},
    ],
    "list_company": [
        {"label": "Dana Dairy EMEA", "value": "dana_dairy_emea"},
        {"label": "Dana Dairy Europe", "value": "dana_dairy_europe"},
        {"label": "Dana Dairy MENA", "value": "dana_dairy_mena"},
        {"label": "Dana Dairy Asia", "value": "dana_dairy_asia"},
        {"label": "Dana Dairy Americas", "value": "dana_dairy_americas"},
    ],
    "list_group": [
        {"label": "A: Infant Formula", "value": "infant_formula"},
        {"label": "B: Consumer Dairy", "value": "consumer_dairy"},
        {"label": "C: Food Service", "value": "food_service"},
        {"label": "D: Dairy Ingredients", "value": "dairy_ingredients"},
        {"label": "E: Infant Formula 25KG", "value": "infant_formula_25kg"},
        {"label": "F: Baby Food PL", "value": "baby_food_pl"},
        {"label": "G: Infant Formula DXB/KR", "value": "infant_formula_dxb_kr"},
        {"label": "H: Baby Cereal 25KG", "value": "baby_cereal_25kg"},
        {"label": "I: Dairy PL", "value": "dairy_pl"},
    ],
}


# -------------------------------------------------------------------
# Inquiry Management Filters
# -------------------------------------------------------------------

INQUIRY_FILTERS = {
    "search": {
        "type": FILTER_TYPES["SEARCH"],
        "placeholder": "Search by ID, customer, email, product, country",
        "label": "Search",
    },
    "phase": {
        "type": FILTER_TYPES["STATIC"],
        "options_key": "phase",
        "label": "All Phases",
    },
    "priority": {
        "type": FILTER_TYPES["STATIC"],
        "options_key": "priority",
        "label": "All Priorities",
    },
    "stage_id": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "stages",
        "label": "All Stages",
    },
    "request_status": {
        "type": FILTER_TYPES["STATIC"],
        "options_key": "status",
        "label": "All Status",
    },
    "user_id": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "assignees",
        "label": "All Assignees",
    },
    "country": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "country",
        "label": "All Countries",
    },
    "customer_id": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "customer_id",
        "label": "All Customers",
    },
    "product_id": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "product_id",
        "label": "All Products",
    },
    "list_company": {
        "type": FILTER_TYPES["STATIC"],
        "options_key": "list_company",
        "label": "All Companies",
    },
    "list_group": {
        "type": FILTER_TYPES["STATIC"],
        "options_key": "list_group",
        "label": "All Groups",
    },
}


# -------------------------------------------------------------------
# Supplier Management Filters
# -------------------------------------------------------------------

SUPPLIER_FILTERS = {
    "search": {
        "type": FILTER_TYPES["SEARCH"],
        "placeholder": "Search by supplier name, email, country",
        "label": "Search",
    },
    "country": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "country",
        "label": "All Countries",
    },
    "company_type": {
        "type": FILTER_TYPES["STATIC"],
        "options_key": "company_type",
        "label": "All Types",
    },
    "category": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "category",
        "label": "All Categories",
    },
    "sub_category": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "sub_category",
        "label": "All Sub Categories",
    },
    "child_category": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "child_category",
        "label": "All Child Categories",
    },
}


# -------------------------------------------------------------------
# Product Management Filters
# -------------------------------------------------------------------

PRODUCT_FILTERS = {
    "search": {
        "type": FILTER_TYPES["SEARCH"],
        "placeholder": "Search by product name or SKU",
        "label": "Search",
    },
    "category": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "category",
        "label": "All Categories",
    },
    "sub_category": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "sub_category",
        "label": "All Sub Categories",
    },
    "child_category": {
        "type": FILTER_TYPES["DYNAMIC"],
        "source": "child_category",
        "label": "All Child Categories",
    },
}


# -------------------------------------------------------------------
# User Management Filters
# -------------------------------------------------------------------

USER_FILTERS = {
    "search": {
        "type": FILTER_TYPES["SEARCH"],
        "placeholder": "Search by user name or email",
        "label": "Search",
    },
    "role": {
        "type": FILTER_TYPES["STATIC"],
        "options_key": "roles",
        "label": "All Roles",
    },
}


# -------------------------------------------------------------------
# Dashboard Filters
# -------------------------------------------------------------------

DASHBOARD_FILTERS = {
    "time_range": {
        "type": FILTER_TYPES["DATE_RANGE"],
        "label": "Time Range",
        "presets": [
            "today",
            "last_7_days",
            "last_30_days",
            "this_month",
            "last_month",
        ],
    },
}


# -------------------------------------------------------------------
# Master Filter Registry (Module → Filters)
# -------------------------------------------------------------------

FILTER_REGISTRY = {
    "inquiry-management": INQUIRY_FILTERS,
    "supplier-management": SUPPLIER_FILTERS,
    "product-management": PRODUCT_FILTERS,
    "users-management": USER_FILTERS,
    "dashboard-management": DASHBOARD_FILTERS,
}


# -------------------------------------------------------------------
# Public Helper
# -------------------------------------------------------------------


def get_filters_for_module(module: str) -> dict:
    """
    Fetch filters for a given module.
    """
    return FILTER_REGISTRY.get(module, {})
