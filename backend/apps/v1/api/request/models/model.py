from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    func,
)
from sqlalchemy.orm import relationship

from apps.v1.api.request.models.attribute import (
    DealOutcome,
    RegistrationStep,
    RequestPhase,
    RequestStatus,
    Source,
    StageStatus,
    Priority,
)

from core.db import Base
from core.db.mixins.timestamp_mixin import TimestampMixin
from core.utils import constant_variable as constant
from apps.v1.api.customer.models.model import Customers


class EnumTypeDecorator(TypeDecorator):
    """
    Custom TypeDecorator for Enum that handles value-based conversion.
    Ensures database values (like 'active', 'completed') are properly converted to enum instances.
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_class, length=50):
        super().__init__(length)
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        """Convert enum to value for database storage."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        if isinstance(value, str):
            # Try to convert string to enum, then return its value
            try:
                return self.enum_class(value.lower()).value
            except ValueError:
                return value
        return value

    def process_result_value(self, value, dialect):
        """Convert database value to enum instance."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value
        if isinstance(value, str):
            # Convert string value to enum by matching value (not name)
            for enum_member in self.enum_class:
                if enum_member.value.lower() == value.lower():
                    return enum_member
            # If no match found, try direct conversion
            try:
                return self.enum_class(value.lower())
            except ValueError:
                # Return the value as-is if no enum match found (graceful degradation)
                return value
        return value


class Requests(Base, TimestampMixin):
    __tablename__ = "requests"

    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    bitrix_id = Column(Integer, nullable=constant.STATUS_FALSE)

    name = Column(String(150), nullable=constant.STATUS_FALSE)
    request_type = Column(String(50), nullable=constant.STATUS_TRUE)
    deal_stage = Column(String(100), nullable=constant.STATUS_FALSE)
    probability = Column(Integer, nullable=constant.STATUS_FALSE)
    currency = Column(String(3), nullable=constant.STATUS_FALSE)
    total = Column(Float, nullable=constant.STATUS_FALSE)
    is_manual_opportunity = Column(
        Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE
    )
    tax_rate = Column(Float, nullable=constant.STATUS_FALSE)
    lead = Column(String(100), nullable=constant.STATUS_FALSE)
    company_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    contact_id = Column(Integer, nullable=constant.STATUS_FALSE)
    estimate_id = Column(Integer, nullable=constant.STATUS_FALSE)
    start_date = Column(DateTime, nullable=constant.STATUS_FALSE)
    end_date = Column(DateTime, nullable=constant.STATUS_FALSE)
    responsible_person = Column(
        Integer, nullable=constant.STATUS_TRUE, comment="Bitrix user ID of responsible person"
    )
    priority = Column(
        EnumTypeDecorator(Priority),
        nullable=constant.STATUS_FALSE,
        default=Priority.LOW,
    )
    assigned_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="User ID mapped from responsible_person Bitrix ID",
    )
    created_by = Column(Integer, nullable=constant.STATUS_FALSE)
    modified_by = Column(Integer, nullable=constant.STATUS_FALSE)
    available_to_everyone = Column(
        Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE
    )
    opened = Column(Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE)
    closed = Column(Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE)
    comment = Column(Text, nullable=constant.STATUS_FALSE)
    additional_information = Column(Text, nullable=constant.STATUS_FALSE)
    pipeline = Column(String(100), nullable=constant.STATUS_FALSE)
    stage_group = Column(String(100), nullable=constant.STATUS_FALSE)
    new_deal = Column(Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE)
    recurring_deal = Column(Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE)
    repeat_deal = Column(Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE)
    repeat_inquiry = Column(String(100), nullable=constant.STATUS_FALSE)
    source_information = Column(String(100), nullable=constant.STATUS_FALSE)
    external_source = Column(String(100), nullable=constant.STATUS_FALSE)
    item_id_in_data_source = Column(Integer, nullable=constant.STATUS_TRUE)
    lead_source = Column(String(100), nullable=constant.STATUS_TRUE)
    moved_by_id = Column(Integer, nullable=constant.STATUS_FALSE)
    moved_time = Column(DateTime, nullable=constant.STATUS_FALSE)
    last_activity_time = Column(DateTime, nullable=constant.STATUS_FALSE)
    ad_system = Column(String(50), nullable=constant.STATUS_FALSE)
    medium = Column(String(50), nullable=constant.STATUS_FALSE)
    ad_campaign_utm = Column(String(200), nullable=constant.STATUS_FALSE)
    campaign_contents = Column(String(200), nullable=constant.STATUS_FALSE)
    campaign_search_term = Column(String(200), nullable=constant.STATUS_FALSE)
    purchase_order = Column(String(50), nullable=constant.STATUS_FALSE)
    last_communication_time = Column(DateTime, nullable=constant.STATUS_FALSE)
    repeat_sale_segment_id = Column(Integer, nullable=constant.STATUS_FALSE)
    last_activity_by = Column(Integer, nullable=constant.STATUS_FALSE)
    forwarder = Column(String(150), nullable=constant.STATUS_FALSE)
    production_date = Column(DateTime, nullable=constant.STATUS_FALSE)
    loading_date = Column(DateTime, nullable=constant.STATUS_FALSE)
    etd = Column(DateTime, nullable=constant.STATUS_FALSE)
    eta = Column(DateTime, nullable=constant.STATUS_FALSE)
    destination_country = Column(String(100), nullable=constant.STATUS_FALSE)
    issuing_bank_ref_number = Column(String(50), nullable=constant.STATUS_FALSE)
    advising_bank_ref_number = Column(String(50), nullable=constant.STATUS_FALSE)
    advised = Column(Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE)
    latest_date_of_shipment = Column(DateTime, nullable=constant.STATUS_FALSE)
    lc_expiry_date = Column(DateTime, nullable=constant.STATUS_FALSE)
    ops = Column(String(100), nullable=constant.STATUS_FALSE)
    buying_company = Column(String(150), nullable=constant.STATUS_FALSE)
    client_payment_term = Column(String(50), nullable=constant.STATUS_FALSE)
    incoterm = Column(String(10), nullable=constant.STATUS_FALSE)
    bl_no = Column(String(50), nullable=constant.STATUS_FALSE)
    doc_to_client_track_id = Column(String(50), nullable=constant.STATUS_FALSE)
    shipment_tracking = Column(String(100), nullable=constant.STATUS_FALSE)
    container_number = Column(String(50), nullable=constant.STATUS_FALSE)
    country_of_destination = Column(String(100), nullable=constant.STATUS_FALSE)
    client_reference_number = Column(String(50), nullable=constant.STATUS_FALSE)
    manufacturer_delivery_terms = Column(String(50), nullable=constant.STATUS_FALSE)
    manufacture_payment_term = Column(String(50), nullable=constant.STATUS_FALSE)
    loaded_container_quantity = Column(Integer, nullable=constant.STATUS_FALSE)
    pi_number = Column(String(50), nullable=constant.STATUS_FALSE)
    export_company = Column(String(150), nullable=constant.STATUS_FALSE)
    port_of_loading = Column(String(100), nullable=constant.STATUS_FALSE)
    port_of_discharge = Column(String(100), nullable=constant.STATUS_FALSE)
    hashtag = Column(JSON, nullable=constant.STATUS_FALSE, default=list)
    manufacturer = Column(JSON, nullable=constant.STATUS_FALSE, default=list)
    shipping_documents = Column(JSON, nullable=constant.STATUS_FALSE, default=list)
    postscript = Column(Text, nullable=constant.STATUS_FALSE)
    advising_bank = Column(String(150), nullable=constant.STATUS_FALSE)
    confirming_bank = Column(String(150), nullable=constant.STATUS_FALSE)
    issuing_bank = Column(String(150), nullable=constant.STATUS_FALSE)
    lc = Column(Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE)
    key_instructions_to_ops = Column(JSON, nullable=constant.STATUS_FALSE, default=list)
    ref_code = Column(String(36), nullable=constant.STATUS_FALSE)
    freight_charges = Column(Float, nullable=constant.STATUS_FALSE)
    shipping_line = Column(String(150), nullable=constant.STATUS_FALSE)
    shipping_date = Column(DateTime, nullable=constant.STATUS_FALSE)
    advance_payment = Column(Float, nullable=constant.STATUS_FALSE)
    lost_reason = Column(String(100), nullable=constant.STATUS_FALSE)
    sample_status = Column(String(50), nullable=constant.STATUS_FALSE)
    buyer_type = Column(String(50), nullable=constant.STATUS_FALSE)
    week_commitment = Column(Integer, nullable=constant.STATUS_FALSE)
    inquiry_date = Column(DateTime, nullable=constant.STATUS_FALSE)
    product_category = Column(JSON, nullable=constant.STATUS_FALSE, default=list)
    origin_accepted = Column(Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE)
    estimated_volume = Column(Integer, nullable=constant.STATUS_FALSE)
    po2factory_customer = Column(
        Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE
    )
    country = Column(String(100), nullable=constant.STATUS_FALSE)
    urgency_level = Column(String(50), nullable=constant.STATUS_FALSE)
    client_size = Column(String(50), nullable=constant.STATUS_FALSE)
    manufacturer_payment_term = Column(String(50), nullable=constant.STATUS_FALSE)
    lead_rank = Column(Integer, nullable=constant.STATUS_FALSE)
    eta_required_by_client = Column(
        Boolean, nullable=constant.STATUS_FALSE, default=constant.STATUS_FALSE
    )
    cargo_readiness_date = Column(DateTime, nullable=constant.STATUS_FALSE)
    next_lots_loading_dates = Column(DateTime, nullable=constant.STATUS_FALSE)
    deal_id = Column(
        String(36),
        nullable=constant.STATUS_FALSE,
        unique=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )

    email = Column(String(100), nullable=constant.STATUS_FALSE)
    email_domain_name = Column(
        JSON,
        nullable=constant.STATUS_TRUE,
        comment="Domain names extracted from email field (JSON array)",
    )
    phone = Column(String(20), nullable=constant.STATUS_FALSE)
    location = Column(String(200), nullable=constant.STATUS_FALSE)
    website = Column(String(200), nullable=constant.STATUS_FALSE)
    bitrix_url = Column(String(500), nullable=constant.STATUS_FALSE)

    source = Column(
        EnumTypeDecorator(Source), nullable=constant.STATUS_FALSE, default=Source.BITRIX
    )
    description = Column(Text, nullable=constant.STATUS_FALSE)
    last_contact = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Last contact date from email sent_at (latest email for this request)",
    )

    request_status = Column(
        EnumTypeDecorator(RequestStatus),
        nullable=constant.STATUS_FALSE,
        default=RequestStatus.NEW_UNCLEAR,
    )
    current_stage_id = Column(
        Integer,
        ForeignKey("stages.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Current active stage ID",
    )
    current_stage_status = Column(
        EnumTypeDecorator(StageStatus),
        nullable=constant.STATUS_FALSE,
        default=StageStatus.NEW_UNCLEAR,
        comment="Current stage status",
    )
    next_stage_id = Column(
        Integer,
        ForeignKey("stages.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Next stage ID in the workflow",
    )
    next_stage_status = Column(
        EnumTypeDecorator(StageStatus),
        nullable=constant.STATUS_TRUE,
        comment="Next stage status",
    )
    phase = Column(
        EnumTypeDecorator(RequestPhase),
        nullable=constant.STATUS_FALSE,
        default=RequestPhase.LEAD,
    )
    observer_bitrixids = Column(
        JSON,
        nullable=constant.STATUS_TRUE,
        comment="List of observer Bitrix user IDs as JSON array",
    )
    observer_ids = Column(
        JSON,
        nullable=constant.STATUS_TRUE,
        comment="List of observer user IDs (mapped from observer_bitrixids) as JSON array",
    )
    company = relationship("Suppliers", foreign_keys=[company_id])
    assigned_to = relationship("Users", foreign_keys=[assigned_by])
    current_stage = relationship(
        "Stage", foreign_keys=[current_stage_id], uselist=False, lazy="select"
    )
    next_stage = relationship("Stage", foreign_keys=[next_stage_id], uselist=False, lazy="select")

    # Relationships for request detail
    request_products = relationship(
        "RequestProductsMapping",
        foreign_keys="RequestProductsMapping.request_id",
        back_populates="request",
        lazy="select",
    )
    request_customers = relationship(
        "RequestCustomersMapping",
        foreign_keys="RequestCustomersMapping.request_id",
        back_populates="request",
        lazy="selectin",
    )
    request_stage_activities = relationship(
        "RequestStageActivity",
        foreign_keys="RequestStageActivity.request_id",
        back_populates="request",
        lazy="selectin",
    )


class Stage(Base, TimestampMixin):
    __tablename__ = "stages"

    id = Column(Integer, primary_key=constant.STATUS_TRUE)
    phase = Column(
        EnumTypeDecorator(RequestPhase),
        nullable=constant.STATUS_FALSE,
        default=RequestPhase.LEAD,
    )
    parent_id = Column(
        Integer,
        ForeignKey("stages.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    stage_name = Column(String(100), nullable=constant.STATUS_FALSE)
    stage_status = Column(
        EnumTypeDecorator(StageStatus),
        nullable=constant.STATUS_FALSE,
        default=StageStatus.NEW_UNCLEAR,
    )
    next_stage_status = Column(
        EnumTypeDecorator(StageStatus),
        nullable=constant.STATUS_TRUE,
    )
    next_stage_id = Column(
        Integer,
        ForeignKey("stages.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    status = Column(
        EnumTypeDecorator(RequestStatus),
        nullable=constant.STATUS_FALSE,
        default=RequestStatus.PENDING,
    )
    order_sequence = Column(Integer, nullable=constant.STATUS_FALSE, default=0)
    is_active = Column(
        Boolean,
        nullable=constant.STATUS_FALSE,
        default=constant.STATUS_TRUE,
    )

    # Note: parent_request relationship removed - incorrect configuration
    # parent_request = relationship("Stage", foreign_keys=[id], back_populates="stages")
    parent_stage = relationship("Stage", foreign_keys=[parent_id], remote_side=[id])
    next_stage = relationship("Stage", foreign_keys=[next_stage_id], remote_side=[id])
    activities = relationship(
        "RequestStageActivity", foreign_keys="RequestStageActivity.stage_id", back_populates="stage"
    )


class RequestStageActivity(Base, TimestampMixin):
    __tablename__ = "request_stage_activities"

    id = Column(Integer, primary_key=constant.STATUS_TRUE)
    request_id = Column(
        Integer,
        ForeignKey("requests.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    stage_id = Column(
        Integer,
        ForeignKey("stages.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    activity_name = Column(String(200), nullable=constant.STATUS_FALSE)
    activity_type = Column(String(50), nullable=constant.STATUS_FALSE)
    registration_step = Column(
        EnumTypeDecorator(RegistrationStep),
        nullable=constant.STATUS_TRUE,
    )
    deal_outcome = Column(
        EnumTypeDecorator(DealOutcome),
        nullable=constant.STATUS_TRUE,
    )
    status = Column(
        EnumTypeDecorator(RequestStatus),
        nullable=constant.STATUS_FALSE,
        default=RequestStatus.PENDING,
    )
    phase = Column(
        EnumTypeDecorator(RequestPhase),
        nullable=constant.STATUS_FALSE,
        default=RequestPhase.INQUIRY,
    )
    order_sequence = Column(Integer, nullable=constant.STATUS_FALSE, default=0)
    is_completed = Column(
        Boolean,
        nullable=constant.STATUS_FALSE,
        default=constant.STATUS_FALSE,
    )
    completed_at = Column(DateTime, nullable=constant.STATUS_TRUE)
    notes = Column(Text, nullable=constant.STATUS_TRUE)

    request = relationship(
        "Requests", foreign_keys=[request_id], back_populates="request_stage_activities"
    )
    stage = relationship("Stage", foreign_keys=[stage_id], back_populates="activities")


class RequestProductsMapping(Base, TimestampMixin):
    __tablename__ = "request_products"
    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    request_id = Column(
        Integer,
        ForeignKey("requests.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # relationships
    request = relationship(
        "Requests", foreign_keys=[request_id], uselist=False, back_populates="request_products"
    )
    product = relationship("Products", foreign_keys=[product_id], uselist=False)


class RequestCustomersMapping(Base, TimestampMixin):
    __tablename__ = "request_customers"
    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    request_id = Column(
        Integer,
        ForeignKey("requests.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # relationships
    request = relationship(
        "Requests", foreign_keys=[request_id], back_populates="request_customers", uselist=False
    )
    customer = relationship("Customers", foreign_keys=[customer_id], uselist=False)
