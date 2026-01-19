"""
Logistic API endpoints.
"""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.logistic.services.logistic_service import LogisticService
from config.db_config import get_async_db
from core.utils import constant_variable

router = APIRouter(prefix=constant_variable.API_V1_PREFIX, tags=["Logistic API"])


@router.get("/logistic/{deal_id}", summary="Get deal logistic details")
async def get_logistic_details(
    deal_id: str = Path(..., description="Deal ID to fetch logistic details"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Fetch deal, supplier, and product details for a given deal.
    """
    service = LogisticService()
    return await service.get_logistic_details(db=db, deal_id=deal_id)


@router.get("/logistic/list", summary="Get full logistic list")
async def get_logistic_list(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get full list of all logistic records from the database.
    Returns a list of all logistic records with deal and product information.
    """
    service = LogisticService()
    return await service.get_logistic_list(db=db)