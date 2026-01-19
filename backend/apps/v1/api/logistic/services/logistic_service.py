"""
Logistic service to fetch deal, supplier, and product details.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.request.models.model import Requests as Deal
from apps.v1.api.products.models.model import Products
from apps.v1.api.suppliers.models.model import Suppliers
from apps.v1.api.logistic.models.model import Logistic
from config.env_config import settings
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class LogisticService:
    async def get_logistic_details(self, db: AsyncSession, deal_id: str) -> Any:
        """
        Fetch deal, supplier, and products for the given deal_id.
        """
        try:
            deal = await self._get_deal(db, deal_id)
            if not deal:
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message="Data not found",
                ).make

            supplier = await self._get_supplier(db, deal)
            products = await self._get_products(db, deal_id)

            data = {
                "deal": self._serialize_deal(deal),
                "supplier": self._serialize_supplier(supplier) if supplier else None,
                "products": products,
            }

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=data,
                message="Data retrieved successfully",
            ).make
        except Exception as exc:
            logger.error(
                f"Unexpected error in get_logistic_details: {exc}", exc_info=True
            )
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    async def _get_deal(self, db: AsyncSession, deal_id: str) -> Optional[Deal]:
        """
        Try multiple identifiers to find the deal:
        - deal_id field (string)
        - numeric id (primary key)
        - bitrix_id (int)
        - uuid
        """
        candidates = []
        # direct match on deal_id (string)
        candidates.append(select(Deal).where(Deal.deal_id == deal_id))

        # numeric primary key
        try:
            numeric_id = int(deal_id)
            candidates.append(select(Deal).where(Deal.id == numeric_id))
            candidates.append(select(Deal).where(Deal.bitrix_id == numeric_id))
        except (TypeError, ValueError):
            pass

        # uuid
        candidates.append(select(Deal).where(Deal.uuid == deal_id))

        for stmt in candidates:
            result = await db.execute(stmt)
            found = result.scalar_one_or_none()
            if found:
                return found
        return None

    async def _get_supplier(self, db: AsyncSession, deal: Deal) -> Optional[Suppliers]:
        # Try by contact id first (if contact holds supplier id)
        supplier = None
        if deal.contact:
            stmt = select(Suppliers).where(Suppliers.id == deal.contact)
            result = await db.execute(stmt)
            supplier = result.scalar_one_or_none()

        # Fallback by company_id foreign key
        if not supplier and deal.company_id:
            stmt = select(Suppliers).where(Suppliers.id == deal.company_id)
            result = await db.execute(stmt)
            supplier = result.scalar_one_or_none()

        return supplier

    async def _get_products(
        self, db: AsyncSession, deal_id: str
    ) -> List[Dict[str, Any]]:
        product_rows = await self._fetch_product_rows(deal_id)
        products: List[Dict[str, Any]] = []

        for row in product_rows:
            # ensure row belongs to this deal
            owner_id = str(row.get("OWNER_ID") or "")
            if owner_id and owner_id != str(deal_id):
                continue

            product_id = row.get("PRODUCT_ID")
            try:
                product_id_int = int(product_id) if product_id is not None else 0
            except (TypeError, ValueError):
                product_id_int = 0

            if not product_id_int:
                # Skip rows without product id
                continue

            product = (
                await self._get_product(db, product_id_int) if product_id_int else None
            )

            products.append({
                "product_id": product_id_int or None,
                "product_name": row.get("PRODUCT_NAME")
                or (product.name if product else None),
                "bitrix_row": {
                    "owner_id": owner_id or None,
                    "price": row.get("PRICE"),
                    "quantity": row.get("QUANTITY"),
                    "measure": row.get("MEASURE_NAME"),
                },
                "product_details": (
                    self._serialize_product(product)
                    if product
                    else {
                        "id": product_id_int or None,
                        "name": row.get("PRODUCT_NAME"),
                        "price": row.get("PRICE"),
                        "quantity": row.get("QUANTITY"),
                        "measure": row.get("MEASURE_NAME"),
                    }
                ),
            })
        return products

    async def _fetch_product_rows(self, deal_id: str) -> List[Dict[str, Any]]:
        url = f"{settings.BITRIX_PRODUCT_ROWS_URL}?id={deal_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                payload = resp.json()
                return payload.get("result", []) if isinstance(payload, dict) else []
        except Exception as exc:
            logger.error(f"Failed to fetch product rows for deal {deal_id}: {exc}")
            return []

    async def _get_product(
        self, db: AsyncSession, product_id: int
    ) -> Optional[Products]:
        # Try by numeric id
        stmt = select(Products).where(Products.id == product_id)
        result = await db.execute(stmt)
        found = result.scalar_one_or_none()
        if found:
            return found

        # Fallback by xml_id (string)
        stmt = select(Products).where(Products.xml_id == str(product_id))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    def _serialize_deal(self, deal: Deal) -> Dict[str, Any]:
        return {
            "id": deal.id,
            "uuid": str(deal.uuid),
            "deal_id": deal.deal_id,
            "name": deal.name,
            "company_id": deal.company_id,
            "contact": deal.contact,
            "bitrix_id": deal.bitrix_id,
            "total": deal.total,
            "currency": deal.currency,
            "start_date": deal.start_date.isoformat() if deal.start_date else None,
            "end_date": deal.end_date.isoformat() if deal.end_date else None,
            "created_at": deal.created_at.isoformat() if deal.created_at else None,
            "updated_at": deal.updated_at.isoformat() if deal.updated_at else None,
        }

    def _serialize_supplier(self, supplier: Suppliers) -> Dict[str, Any]:
        return {
            "id": supplier.id,
            "uuid": str(supplier.uuid),
            "company_name": supplier.company_name,
            "email": supplier.email,
            "phone": supplier.phone,
            "website": supplier.website,
            "country": supplier.country,
            "created_on": supplier.created_on.isoformat()
            if supplier.created_on
            else None,
            "modified_on": supplier.modified_on.isoformat()
            if supplier.modified_on
            else None,
        }

    def _serialize_product(self, product: Products) -> Dict[str, Any]:
        return {
            "id": product.id,
            "uuid": str(product.uuid),
            "name": product.name,
            "supplier_id": product.supplier_id,
            "supplier_name": product.supplier_name,
            "code": product.code,
            "price": product.price,
            "currency_id": product.currency_id,
            "description": product.description,
            "active": product.active,
            "date_create": product.date_create.isoformat()
            if product.date_create
            else None,
            "timestamp_x": product.timestamp_x.isoformat()
            if product.timestamp_x
            else None,
        }

    async def create_logistic_list(self, db: AsyncSession, deal_id: str) -> Any:
        """
        Create logistic records for a given deal_id.
        Fetches deal and products, then stores them in the logistic table.
        Returns a list of created/retrieved logistic records.
        """
        try:
            # Get deal
            deal = await self._get_deal(db, deal_id)
            if not deal:
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message="Deal not found",
                ).make

            # Get products for this deal
            products_data = await self._get_products(db, deal_id)
            if not products_data:
                return StandardResponse(
                    status=constant_variable.STATUS_FAIL,
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=constant_variable.STATUS_NULL,
                    message="No products found for this deal",
                ).make

            # Get deal UUID for foreign key
            deal_uuid = str(deal.uuid)
            created_records = []

            # Create logistic records for each product
            for product_data in products_data:
                product_id_int = product_data.get("product_id")
                product_details = product_data.get("product_details", {})
                product_uuid = product_details.get("uuid")

                # If UUID not in product_details, try to get product from database
                if not product_uuid and product_id_int:
                    product = await self._get_product(db, product_id_int)
                    if product:
                        product_uuid = str(product.uuid)
                    else:
                        # Skip if product doesn't exist in database
                        logger.warning(
                            f"Product {product_id_int} not found in database, skipping"
                        )
                        continue

                if not product_uuid:
                    # Skip if product doesn't have UUID
                    logger.warning(
                        f"Product {product_id_int} does not have UUID, skipping"
                    )
                    continue

                # Check if logistic record already exists
                stmt = select(Logistic).where(
                    Logistic.deal_id == deal_uuid, Logistic.product_id == product_uuid
                )
                result = await db.execute(stmt)
                existing_logistic = result.scalar_one_or_none()

                if existing_logistic:
                    # Record already exists, add to list
                    created_records.append(self._serialize_logistic(existing_logistic))
                else:
                    # Create new logistic record
                    try:
                        new_logistic = Logistic(
                            deal_id=deal_uuid, product_id=product_uuid
                        )
                        db.add(new_logistic)
                        await db.flush()  # Flush to get the ID
                        await db.refresh(new_logistic)
                        created_records.append(self._serialize_logistic(new_logistic))
                    except Exception as exc:
                        logger.error(
                            f"Error creating logistic record for product {product_uuid}: {exc}",
                            exc_info=True,
                        )
                        # Don't rollback here, continue with other records
                        # Rollback will happen at the end if needed
                        continue

            # Commit all changes
            await db.commit()

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_201_CREATED,
                data=created_records,
                message=f"Successfully created {len(created_records)} logistic record(s)",
            ).make

        except Exception as exc:
            logger.error(
                f"Unexpected error in create_logistic_list: {exc}", exc_info=True
            )
            await db.rollback()
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    async def get_logistic_list(self, db: AsyncSession) -> Any:
        """
        Get full list of all logistic records from the database.
        Returns a list of all logistic records with deal and product information.
        """
        try:
            # Fetch all logistic records with relationships
            stmt = (
                select(Logistic)
                .options(selectinload(Logistic.deal), selectinload(Logistic.product))
                .order_by(Logistic.created_at.desc())
            )

            result = await db.execute(stmt)
            logistic_records = result.scalars().all()

            if not logistic_records:
                return StandardResponse(
                    status=constant_variable.STATUS_SUCCESS,
                    status_code=status.HTTP_200_OK,
                    data=[],
                    message="No logistic records found",
                ).make

            # Serialize all records
            serialized_records = []
            for logistic in logistic_records:
                record = self._serialize_logistic_with_details(logistic)
                serialized_records.append(record)

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=serialized_records,
                message=f"Successfully retrieved {len(serialized_records)} logistic record(s)",
            ).make

        except Exception as exc:
            logger.error(f"Unexpected error in get_logistic_list: {exc}", exc_info=True)
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make

    def _serialize_logistic(self, logistic: Logistic) -> Dict[str, Any]:
        """Serialize logistic record for response."""
        return {
            "id": logistic.id,
            "product_id": logistic.product_id,
            "cartons_per_pallet": logistic.cartons_per_pallet,
            "loading_quantities": logistic.loading_quantities,
            "transport_delivery_conditions_temperature": logistic.transport_delivery_conditions_temperature,
            "storage_conditions_temperature": logistic.storage_conditions_temperature,
            "carton_dimensions": logistic.carton_dimensions,
            "pallet_dimensions": logistic.pallet_dimensions,
            "term_of_delivery": logistic.term_of_delivery,
            "created_at": logistic.created_at.isoformat()
            if logistic.created_at
            else None,
            "updated_at": logistic.updated_at.isoformat()
            if logistic.updated_at
            else None,
        }

    def _serialize_logistic_with_details(self, logistic: Logistic) -> Dict[str, Any]:
        """Serialize logistic record with product details."""
        record = {
            "id": logistic.id,
            "product_id": logistic.product_id,
            "cartons_per_pallet": logistic.cartons_per_pallet,
            "loading_quantities": logistic.loading_quantities,
            "transport_delivery_conditions_temperature": logistic.transport_delivery_conditions_temperature,
            "storage_conditions_temperature": logistic.storage_conditions_temperature,
            "carton_dimensions": logistic.carton_dimensions,
            "pallet_dimensions": logistic.pallet_dimensions,
            "term_of_delivery": logistic.term_of_delivery,
            "created_at": logistic.created_at.isoformat()
            if logistic.created_at
            else None,
            "updated_at": logistic.updated_at.isoformat()
            if logistic.updated_at
            else None,
        }

        # Add product details if available
        if logistic.product:
            record["product"] = self._serialize_product(logistic.product)
        else:
            record["product"] = None

        return record
