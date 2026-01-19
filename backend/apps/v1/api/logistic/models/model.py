import json
import logging
from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum as SQLEnum,
    Text,
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
                    f"Failed to parse JSON value (logistic_id may be affected): {str(e)[:100]}. "
                    f"Returning None. Value preview: {str(value)[:100]}"
                )
                return None

        # For any other type, return as-is
        return value


class Logistic(Base, TimestampMixin):
    __tablename__ = "logistic"

    id = Column(Integer, primary_key=constant.STATUS_TRUE, index=constant.STATUS_TRUE)
    cartons_per_pallet = Column(Integer, nullable=constant.STATUS_FALSE)
    loading_quantities = Column(SafeJSON, nullable=constant.STATUS_FALSE)
    transport_delivery_conditions_temperature = Column(String(100), nullable=constant.STATUS_FALSE)
    storage_conditions_temperature = Column(String(100), nullable=constant.STATUS_FALSE)
    carton_dimensions = Column(String(100), nullable=constant.STATUS_FALSE)
    pallet_dimensions = Column(String(100), nullable=constant.STATUS_FALSE)
    term_of_delivery = Column(String(100), nullable=constant.STATUS_FALSE)
    loading_address = Column(String(255), nullable=constant.STATUS_FALSE)
    lead_time_to_print_packing_material = Column(String(100), nullable=constant.STATUS_FALSE)
    lead_time_to_reorder_packing_material = Column(String(100), nullable=constant.STATUS_FALSE)
    moq_packaging_matereal = Column(Integer, nullable=constant.STATUS_FALSE)
    moq_production = Column(Integer, nullable=constant.STATUS_FALSE)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=constant.STATUS_FALSE)

    product = relationship("Products", foreign_keys=[product_id], uselist=False)