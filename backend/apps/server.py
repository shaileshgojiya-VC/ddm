"""
FastAPI application server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all models to ensure they're registered with SQLAlchemy Base
# This is critical for relationship resolution
from apps.v1.api.auth.models.model import (  # noqa: F401
    Users,
    Roles,
    Modules,
    ActivityLog,
    Permission,
    RolePermission,
)

# from apps.v1.api.deal.models.model import Deal, DealLifecycle, DealAction, DealAssignment, Lead  # noqa: F401
from apps.v1.api.suppliers.models.model import Suppliers  # noqa: F401
from apps.v1.api.products.models.model import Products  # noqa: F401
from apps.v1.api.customer.models.model import Customers  # noqa: F401
from apps.v1.api.request.models.model import (  # noqa: F401
    Requests,
    Stage,
    RequestStageActivity,
    RequestProductsMapping,
    RequestCustomersMapping,
)

from apps.v1.api.auth.view import router as auth_router
from apps.v1.api.modules.view import router as modules_router
from apps.v1.api.role.view import router as role_router
from apps.v1.api.suppliers.view import router as suppliers_router
from apps.v1.api.request.view import router as request_router

# from apps.v1.api.deal.view import router as deal_router
# from apps.v1.api.deal.view import lead_router as lead_router
from apps.v1.api.products.view import router as product_router
from apps.v1.api.logistic.view import router as logistic_router
from apps.v1.api.api_filters.view import router as filters_router
from apps.v1.api.bitrix.view import router as bitrix_router
from config.cors import get_cors_config

app = FastAPI(
    title="Welcome to Dana Dairy Backend",
    description="Dana Dairy Backend API",
    version="0.1.0",
)

# CORS configuration
cors_config = get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Include routers
app.include_router(auth_router)
app.include_router(modules_router)
app.include_router(role_router)
app.include_router(suppliers_router)
# app.include_router(deal_router)
# app.include_router(lead_router)
app.include_router(product_router)
app.include_router(logistic_router)
app.include_router(request_router)
app.include_router(filters_router)
app.include_router(bitrix_router)


@app.get("/")
async def root():
    return {"message": "Connected Successfully to Dana Dairy Backend Server is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
