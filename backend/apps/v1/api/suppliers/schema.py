"""
Pydantic schemas for supplier API responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SupplierFullSchema(BaseModel):
    """Full supplier model for API responses."""

    id: int
    bitrix_id: Optional[int] = None
    uuid: Optional[str] = None
    company_type: Optional[str] = None
    company_name: Optional[str] = None
    logo: Optional[str] = None
    lead: Optional[int] = None
    has_phone: bool = False
    has_email: bool = False
    has_open_channel: bool = False
    responsible_person: Optional[str] = None
    created_by: Optional[str] = None
    modified_by: Optional[str] = None
    payment_details: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue: Optional[int] = None
    currency: Optional[str] = None
    employees: Optional[str] = None
    comment: Optional[str] = None
    created_on: Optional[datetime] = None
    modified_on: Optional[datetime] = None
    available_to_everyone: bool = False
    my_company: bool = False
    external_source: Optional[str] = None
    original_version: Optional[int] = None
    street_address: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    region: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    location_address_id: Optional[int] = None
    legal_address: Optional[str] = None
    billing_address: Optional[str] = None
    billing_address_line_2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_zip: Optional[str] = None
    billing_region: Optional[str] = None
    billing_state: Optional[str] = None
    billing_country: Optional[str] = None
    billing_country_code: Optional[str] = None
    legal_address_location_address_id: Optional[int] = None
    ad_system: Optional[str] = None
    medium: Optional[str] = None
    ad_campaign_utm: Optional[str] = None
    campaign_contents: Optional[str] = None
    campaign_search_term: Optional[str] = None
    last_timeline_activity_added_by: Optional[str] = None
    last_updated_on: Optional[datetime] = None
    last_contact: Optional[str] = None
    type_of_buyer: Optional[str] = None
    prefix: Optional[str] = None
    certificates: Optional[str] = None
    ops: Optional[str] = None
    health_mark: Optional[str] = None
    hashtag: Optional[str] = None
    product_category: Optional[str] = None
    week_commitment: Optional[int] = None
    annual_order_volume: Optional[int] = None
    lost_reason: Optional[str] = None
    date_of_inquiry: Optional[datetime] = None
    origin_accepted: bool = False
    estimated_volume: Optional[int] = None
    purchased: bool = False
    stars: Optional[int] = None
    projected: Optional[int] = None
    factory_certificates: Optional[str] = None
    lead_rank: Optional[int] = None
    new_list: Optional[str] = None
    new_text: Optional[str] = None
    products_manufactured: Optional[str] = None
    supplier_name: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    messenger: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

