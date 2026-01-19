import json
import logging
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    func,
    TypeDecorator,
)
from sqlalchemy.orm import relationship

from core.db import Base
from core.db.mixins.timestamp_mixin import TimestampMixin
from core.utils import constant_variable as constant

logger = logging.getLogger(__name__)


class SafeJSON(TypeDecorator):
    """
    Custom JSON type that handles malformed JSON gracefully.
    Uses Text as base to avoid SQLAlchemy's JSON processor that fails on malformed JSON.
    Returns None if JSON parsing fails instead of raising an exception.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Process value when binding to database."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to serialize JSON value: {str(e)[:100]}. Returning None.")
                return None
        if isinstance(value, str):
            # If it's already a string, validate it's valid JSON
            try:
                json.loads(value)  # Validate
                return value
            except (json.JSONDecodeError, TypeError, ValueError):
                # If invalid, try to serialize it as a string value
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """Process JSON value from database, handling malformed JSON."""
        if value is None:
            return None

        # If already parsed (dict/list), return as-is
        if isinstance(value, (dict, list)):
            return value

        # If it's a string, try to parse it
        if isinstance(value, str):
            # Skip if empty string
            if not value.strip():
                return None
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(
                    f"Failed to parse JSON value (supplier_id may be affected): {str(e)[:100]}. "
                    f"Returning None. Value preview: {str(value)[:100]}"
                )
                return None

        # For any other type, return as-is
        return value


class Suppliers(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    bitrix_id = Column(Integer, nullable=constant.STATUS_FALSE)
    company_name = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Supplier company name"
    )
    has_products = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether supplier has products (Yes/No)",
    )
    linked_products_count = Column(
        Integer,
        nullable=constant.STATUS_TRUE,
        default=0,
        comment="Number of linked products",
    )
    linked_products = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="List of linked product names",
    )
    company_type = Column(String(255), nullable=constant.STATUS_TRUE, comment="Type of company")
    logo = Column(
        SafeJSON, nullable=constant.STATUS_TRUE, comment="Company logo file URLs with domain prefix"
    )
    lead = Column(Integer, nullable=constant.STATUS_TRUE, comment="Lead identifier")
    has_phone = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether has phone number",
    )
    has_email = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether has email address",
    )
    has_open_channel = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether has open channel",
    )
    responsible_person = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Responsible person Id"
    )
    created_by = Column(String(255), nullable=constant.STATUS_TRUE, comment="User who created")
    modified_by = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="User who last modified"
    )
    assigned_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="User ID mapped from responsible_person Bitrix ID",
    )
    generated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="User ID mapped from created_by Bitrix ID",
    )
    updated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="User ID mapped from modified_by Bitrix ID",
    )
    payment_details = Column(String(255), nullable=constant.STATUS_TRUE, comment="Payment details")
    industry = Column(String(255), nullable=constant.STATUS_TRUE, comment="Industry Code")
    annual_revenue = Column(Integer, nullable=constant.STATUS_TRUE, comment="Annual revenue")
    currency = Column(String(255), nullable=constant.STATUS_TRUE, comment="Currency code")
    employees = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="Number of employees (e.g., EMPLOYEES_2)",
    )
    comment = Column(Text, nullable=constant.STATUS_TRUE, comment="Supplier comment")
    created_on = Column(DateTime, nullable=constant.STATUS_TRUE, comment="Creation date")
    modified_on = Column(
        DateTime, nullable=constant.STATUS_TRUE, comment="Last modification timestamp"
    )
    available_to_everyone = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether available to everyone",
    )
    my_company = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether my company",
    )
    external_source = Column(String(255), nullable=constant.STATUS_TRUE, comment="External source")
    original_version = Column(Integer, nullable=constant.STATUS_TRUE, comment="Original version")
    street_address = Column(String(255), nullable=constant.STATUS_TRUE, comment="Street address")
    address_line_2 = Column(String(255), nullable=constant.STATUS_TRUE, comment="Address line 2")
    city = Column(String(255), nullable=constant.STATUS_TRUE, comment="City")
    zip = Column(String(255), nullable=constant.STATUS_TRUE, comment="Zip code")
    region = Column(String(255), nullable=constant.STATUS_TRUE, comment="Region")
    state = Column(String(255), nullable=constant.STATUS_TRUE, comment="State / Province")
    country = Column(
        Text, nullable=constant.STATUS_TRUE, comment="Country (may include coordinates)"
    )
    country_code = Column(String(255), nullable=constant.STATUS_TRUE, comment="Country code")
    location_address_id = Column(
        Integer, nullable=constant.STATUS_TRUE, comment="Location address identifier"
    )
    legal_address = Column(String(255), nullable=constant.STATUS_TRUE, comment="Legal address")
    billing_address = Column(String(255), nullable=constant.STATUS_TRUE, comment="Billing address")
    billing_address_line_2 = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Billing address line 2"
    )
    billing_city = Column(String(255), nullable=constant.STATUS_TRUE, comment="Billing city")
    billing_zip = Column(String(255), nullable=constant.STATUS_TRUE, comment="Billing zip code")
    billing_region = Column(String(255), nullable=constant.STATUS_TRUE, comment="Billing region")
    billing_state = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Billing State / Province"
    )
    billing_country = Column(String(255), nullable=constant.STATUS_TRUE, comment="Billing country")
    billing_country_code = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Billing country code"
    )
    legal_address_location_address_id = Column(
        Integer,
        nullable=constant.STATUS_TRUE,
        comment="Legal address location address identifier",
    )
    ad_system = Column(String(255), nullable=constant.STATUS_TRUE, comment="Ad system")
    medium = Column(String(255), nullable=constant.STATUS_TRUE, comment="Medium")
    ad_campaign_utm = Column(String(255), nullable=constant.STATUS_TRUE, comment="Ad campaign UTM")
    campaign_contents = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Campaign contents"
    )
    campaign_search_term = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Campaign search term"
    )
    last_timeline_activity_added_by = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="User who last added timeline activity",
    )
    last_updated_on = Column(
        DateTime, nullable=constant.STATUS_TRUE, comment="Last update timestamp"
    )
    last_contact = Column(String(255), nullable=constant.STATUS_TRUE, comment="Last contact")
    type_of_buyer = Column(String(255), nullable=constant.STATUS_TRUE, comment="Type of Buyer")
    prefix = Column(String(255), nullable=constant.STATUS_TRUE, comment="Prefix")
    certificates = Column(
        JSON,
        nullable=constant.STATUS_TRUE,
        comment="Certificates array with showUrl and downloadUrl",
    )
    ops = Column(String(255), nullable=constant.STATUS_TRUE, comment="OPS")
    health_mark = Column(String(255), nullable=constant.STATUS_TRUE, comment="Health Mark")
    hashtag = Column(Text, nullable=constant.STATUS_TRUE, comment="#TAG (can be boolean or string)")
    product_category = Column(
        Text, nullable=constant.STATUS_TRUE, comment="Product Category (can be boolean or string)"
    )
    week_commitment = Column(Integer, nullable=constant.STATUS_TRUE, comment="Week commitment")
    annual_order_volume = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Annual Order Volume (FCLs)"
    )
    lost_reason = Column(String(255), nullable=constant.STATUS_TRUE, comment="Lost reason")
    date_of_inquiry = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        comment="Date of Inquiry (inquiry date / cold contact date)",
    )
    origin_accepted = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether origin is accepted",
    )
    estimated_volume = Column(Integer, nullable=constant.STATUS_TRUE, comment="Estimated volume")
    purchased = Column(
        Boolean,
        nullable=constant.STATUS_TRUE,
        default=constant.STATUS_FALSE,
        comment="Whether purchased",
    )
    stars = Column(String(255), nullable=constant.STATUS_TRUE, comment="Stars")
    projected = Column(String(255), nullable=constant.STATUS_TRUE, comment="Projected")
    factory_certificates = Column(
        Text,
        nullable=constant.STATUS_TRUE,
        comment="Factory certificates: a. ISO b. HACCP b. FSSC c. GMP d. LICENSE",
    )
    lead_rank = Column(String(255), nullable=constant.STATUS_TRUE, comment="Lead Rank")
    new_list = Column(String(255), nullable=constant.STATUS_TRUE, comment="New list")
    new_text = Column(
        Text, nullable=constant.STATUS_TRUE, comment="New text (can be boolean or string)"
    )
    products_manufactured = Column(
        Text, nullable=constant.STATUS_TRUE, comment="Products manufactured"
    )
    supplier_name = Column(String(255), nullable=constant.STATUS_TRUE, comment="Supplier Name")
    email = Column(
        SafeJSON,
        nullable=constant.STATUS_TRUE,
        comment="E-mail array with VALUE_TYPE, VALUE, TYPE_ID",
    )
    email_domain_name = Column(
        SafeJSON,
        nullable=constant.STATUS_TRUE,
        comment="Domain names extracted from email (same structure as email field)",
    )
    website = Column(
        SafeJSON,
        nullable=constant.STATUS_TRUE,
        comment="Website array with VALUE_TYPE, VALUE, TYPE_ID",
    )
    # assignee = Column(String(255), nullable=constant.STATUS_TRUE, comment="Assignee")
    phone = Column(
        SafeJSON,
        nullable=constant.STATUS_TRUE,
        comment="Phone array with ID, VALUE_TYPE, VALUE, TYPE_ID",
    )
    messenger = Column(String(255), nullable=constant.STATUS_TRUE, comment="Messenger")
    rq_vat_id = Column(String(255), nullable=constant.STATUS_TRUE, comment="RQ VAT ID")
    registration_number = Column(
        String(255), nullable=constant.STATUS_TRUE, comment="Registration Number"
    )

    # Relationships
    product_suppliers = relationship(
        "ProductSupplierMapping",
        foreign_keys="ProductSupplierMapping.supplier_id",
        back_populates="supplier",
        lazy="selectin",
    )
    supplier_emails = relationship(
        "SupplierEmail",
        foreign_keys="SupplierEmail.supplier_id",
        back_populates="supplier",
        lazy="selectin",
    )

    # User relationships
    assigned_by_user = relationship(
        "Users", foreign_keys="Suppliers.assigned_by", back_populates="assigned_suppliers"
    )
    generated_by_user = relationship(
        "Users", foreign_keys="Suppliers.generated_by", back_populates="generated_suppliers"
    )
    updated_by_user = relationship(
        "Users", foreign_keys="Suppliers.updated_by", back_populates="updated_suppliers"
    )


class ProductSupplierMapping(Base, TimestampMixin):
    """
    Product Supplier mapping model.

    Simple mapping table between products and suppliers.
    """

    __tablename__ = "product_suppliers"
    __table_args__ = {"extend_existing": True}

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    name = Column(String(255), nullable=constant.STATUS_TRUE, comment="Name")

    # relationships
    product = relationship(
        "Products",
        foreign_keys=[product_id],
        back_populates="product_suppliers",
        uselist=False,
    )
    supplier = relationship(
        "Suppliers",
        foreign_keys=[supplier_id],
        back_populates="product_suppliers",
        uselist=False,
    )


class SupplierEmail(Base, TimestampMixin):
    __tablename__ = "supplier_emails"
    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    email_id = Column(
        Integer,
        ForeignKey("emails.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )

    # relationships
    supplier = relationship(
        "Suppliers",
        foreign_keys=[supplier_id],
        back_populates="supplier_emails",
        uselist=False,
    )
    emails = relationship(
        "Emails",
        primaryjoin="SupplierEmail.email_id == Emails.id",
        foreign_keys=[email_id],
        back_populates="supplier_emails",
        uselist=False,
    )


class Documents(Base, TimestampMixin):
    __tablename__ = "documents"
    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    path = Column(Text, nullable=constant.STATUS_TRUE, comment="Path")  # Changed to Text to support full URLs (Azure blob URLs can be long)
    url = Column(Text, nullable=constant.STATUS_TRUE, comment="URL")  # Changed to Text to support long URLs
    file_name = Column(String(255), nullable=constant.STATUS_TRUE, comment="File name")
    file_type = Column(String(255), nullable=constant.STATUS_TRUE, comment="File type")
    doc_type = Column(String(255), nullable=constant.STATUS_TRUE, comment="Document type")
    file_size = Column(Integer, nullable=constant.STATUS_TRUE, comment="File size")
    content_id = Column(String(500), nullable=constant.STATUS_TRUE, comment="Content ID from email attachment (for inline images)")
    source = Column(String(255), nullable=constant.STATUS_TRUE, comment="Source")
    mapping_id = Column(Integer, nullable=constant.STATUS_TRUE, comment="Mapping ID")
    source_table = Column(String(255), nullable=constant.STATUS_TRUE, comment="Source table")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
