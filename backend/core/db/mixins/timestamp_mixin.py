"""
Timestamp mixin for models.
"""

from sqlalchemy import Column, DateTime, func


class TimestampMixin:
    """Mixin for adding timestamp fields."""

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
