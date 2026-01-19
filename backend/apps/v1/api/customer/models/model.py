from core.db import Base
from core.db.mixins.timestamp_mixin import TimestampMixin
from sqlalchemy import Column, Integer, String, JSON
from core.utils import constant_variable as constant


class Customers(Base, TimestampMixin):
    __tablename__ = "customers"
    id = Column(
        Integer,
        primary_key=constant.STATUS_TRUE,
        autoincrement=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    bitrix_id = Column(Integer, nullable=constant.STATUS_TRUE)
    company_name = Column(String(256), nullable=constant.STATUS_TRUE, comment="Company Name")
    full_name = Column(String(256), nullable=constant.STATUS_TRUE, comment="Full Name")
    country = Column(String(255), nullable=constant.STATUS_TRUE, comment="Country")
    # Store multiple email addresses as a JSON array (e.g., ["a@x.com", "b@y.com"])
    email_ids = Column(JSON, nullable=constant.STATUS_TRUE, comment="Email IDs as JSON array")
    # Store domain names extracted from email_ids (e.g., ["x.com", "y.com"])
    email_ids_domain_name = Column(
        JSON, nullable=constant.STATUS_TRUE, comment="Domain names extracted from email_ids"
    )
