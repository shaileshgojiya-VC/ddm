"""
Service to create new customers.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from apps.v1.api.customer.models.model import Customers
from apps.v1.api.customer.serializer import ContactWebhookSerializer

logger = logging.getLogger(__name__)


class CreateCustomerService:
    """Service for creating new customers."""

    async def create_customer(self, db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single customer from incoming JSON payload."""
        logger.info("Creating new customer")
        
        # Normalize and validate the payload using serializer
        serializer = ContactWebhookSerializer()
        mapped = serializer.load(payload)

        # Filter out auto-generated fields
        excluded_fields = {"id", "created_at", "updated_at", "deleted_at"}
        clean_data = {k: v for k, v in mapped.items() if k not in excluded_fields}
        clean_data.pop('id', None)

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

        try:
            # Create customer instance
            await db.execute(insert(Customers).values(clean_data))
            await db.commit()
            
            # Fetch the created customer
            from sqlalchemy import select
            stmt = select(Customers).where(
                Customers.bitrix_id == clean_data.get("bitrix_id")
            ).order_by(Customers.id.desc()).limit(1)
            result = await db.execute(stmt)
            customer = result.scalar_one_or_none()
            
            if not customer:
                raise HTTPException(status_code=500, detail="Customer created but could not be retrieved")
            
            logger.info(f"Customer created successfully with id: {customer.id}")
            
            result = {
                "id": customer.id,
                "bitrix_id": customer.bitrix_id,
                "name": customer.name or customer.full_name,
                "email_ids": customer.email_ids,
                "country": customer.country,
                "company_name": getattr(customer, "company_name", None),
            }
            
            # After successful creation, sync with webhook_data_service if bitrix_id exists
            if customer.bitrix_id:
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
                        bitrix_id=str(customer.bitrix_id),
                        mapping=mapping
                    )
                    logger.info(f"Synced customer {customer.id} with webhook_data_service")
                except Exception as e:
                    # Log error but don't fail the create operation
                    logger.warning(f"Failed to sync customer {customer.id} with webhook_data_service: {e}")
            
            return result
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating customer: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")

