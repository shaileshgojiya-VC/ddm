"""
Service to update customers.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.customer.models.model import Customers
from apps.v1.api.customer.serializer import ContactWebhookSerializer

logger = logging.getLogger(__name__)


class UpdateCustomerService:
    """Service for updating existing customers."""

    async def update_customer(
        self, db: AsyncSession, customer_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a single customer by database id."""
        try:
            db_id = int(customer_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Customer ID must be a valid integer",
            )

        # Normalize and validate incoming payload
        serializer = ContactWebhookSerializer()
        mapped = serializer.load(payload)

        # Filter out auto-generated fields
        excluded_fields = {"id", "created_at", "updated_at", "deleted_at"}
        clean_data = {k: v for k, v in mapped.items() if k not in excluded_fields}
        clean_data.pop('id', None)

        if not clean_data:
            raise HTTPException(
                status_code=400,
                detail="No updatable fields provided",
            )

        # Handle email field - convert to email_ids JSON array if needed
        if "email" in clean_data and clean_data["email"]:
            email_value = clean_data.pop("email")
            if isinstance(email_value, list):
                clean_data["email_ids"] = email_value
            elif isinstance(email_value, str):
                clean_data["email_ids"] = [email_value]
            else:
                clean_data["email_ids"] = []

        # Handle name field mapping
        if "name" not in clean_data and "full_name" in clean_data:
            clean_data["name"] = clean_data.pop("full_name")

        # Check if customer exists
        stmt = select(Customers).where(Customers.id == db_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        try:
            # Update customer
            update_stmt = (
                update(Customers)
                .where(Customers.id == db_id)
                .values(**clean_data)
            )
            await db.execute(update_stmt)
            await db.commit()

            # Fetch updated customer
            result = await db.execute(stmt)
            updated_customer = result.scalar_one_or_none()

            if not updated_customer:
                raise HTTPException(status_code=500, detail="Customer updated but could not be retrieved")

            logger.info(f"Customer {customer_id} updated successfully")
            result = {
                "id": updated_customer.id,
                "bitrix_id": updated_customer.bitrix_id,
                "name": updated_customer.name or updated_customer.full_name,
                "email_ids": updated_customer.email_ids,
                "country": updated_customer.country,
                "company_name": getattr(updated_customer, "company_name", None),
            }
            
            # After successful update, sync with webhook_data_service if bitrix_id exists
            if updated_customer.bitrix_id:
                try:
                    from apps.v1.api.bitrix.services.webhook_data_service import WebhookDataService
                    webhook_service = WebhookDataService()
                    # Extract mapping data from payload if present
                    mapping = payload.get("mapping") or payload.get("mappings")
                    if isinstance(mapping, dict):
                        mapping = [mapping]
                    elif not isinstance(mapping, list):
                        mapping = None
                    
                    # Call webhook service to sync (this handles mappings, etc.)
                    await webhook_service.update(
                        db=db,
                        table_name="customers",
                        data=clean_data,
                        bitrix_id=str(updated_customer.bitrix_id),
                        mapping=mapping
                    )
                    logger.info(f"Synced customer {updated_customer.id} with webhook_data_service")
                except Exception as e:
                    # Log error but don't fail the update operation
                    logger.warning(f"Failed to sync customer {updated_customer.id} with webhook_data_service: {e}")
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating customer {customer_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(e)}")

