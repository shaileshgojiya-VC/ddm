"""
Authentication models.
"""

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    func,
)
from sqlalchemy.orm import relationship

from apps.v1.api.auth.models.attribute import Action, Status
from config.db_config import Base
from core.db.mixins.timestamp_mixin import TimestampMixin
from core.utils import constant_variable as constant


class EnumTypeDecorator(TypeDecorator):
    """
    Custom TypeDecorator for Enum that handles value-based conversion.
    Ensures database values (like 'active') are properly converted to enum instances.
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_class, length=20):
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
                return value
        return value


class Users(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=constant.STATUS_TRUE, index=constant.STATUS_TRUE)
    bitrix_id = Column(Integer, nullable=constant.STATUS_FALSE)

    parent_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )

    name = Column(String(255), nullable=constant.STATUS_FALSE)
    email = Column(
        String(255),
        unique=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        nullable=constant.STATUS_FALSE,
    )
    email_domain_name = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Domain name extracted from email",
    )
    phone_number = Column(String(20), nullable=constant.STATUS_TRUE)
    location = Column(String(255), nullable=constant.STATUS_TRUE)
    profile_image_url = Column(String(500), nullable=constant.STATUS_TRUE)

    hashed_password = Column(String(255), nullable=constant.STATUS_FALSE)
    joined_at = Column(DateTime, nullable=constant.STATUS_FALSE)

    role_id = Column(
        Integer,
        ForeignKey("roles.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )

    status = Column(
        EnumTypeDecorator(Status, length=20),
        nullable=constant.STATUS_FALSE,
        default=Status.ACTIVE,
    )

    reset_token = Column(
        String(255), nullable=constant.STATUS_TRUE, index=constant.STATUS_TRUE
    )
    reset_token_expires_at = Column(DateTime, nullable=constant.STATUS_TRUE)

    # Email verification fields
    pending_email = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        comment="New email awaiting verification",
    )
    email_verified_at = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        comment="Timestamp when email was verified",
    )
    pending_email_token = Column(
        String(255),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        comment="Token for verifying new email",
    )
    pending_email_token_expires_at = Column(
        DateTime,
        nullable=constant.STATUS_TRUE,
        comment="Expiry time for email verification token",
    )

    role = relationship("Roles", back_populates="users")
    parent_user = relationship(
        "Users", foreign_keys=[parent_user_id], remote_side=[id], backref="child_users"
    )
    creator = relationship(
        "Users", foreign_keys=[created_by], remote_side=[id], backref="created_users"
    )

    activity_logs = relationship("ActivityLog", back_populates="user")
    assigned_suppliers = relationship(
        "Suppliers",
        foreign_keys="Suppliers.assigned_by",
        back_populates="assigned_by_user",
    )
    generated_suppliers = relationship(
        "Suppliers",
        foreign_keys="Suppliers.generated_by",
        back_populates="generated_by_user",
    )
    updated_suppliers = relationship(
        "Suppliers",
        foreign_keys="Suppliers.updated_by",
        back_populates="updated_by_user",
    )


class Roles(Base, TimestampMixin):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=constant.STATUS_TRUE, index=constant.STATUS_TRUE)

    name = Column(String(100), nullable=constant.STATUS_FALSE)
    description = Column(String(500), nullable=constant.STATUS_TRUE)

    module_list = Column(JSON, nullable=constant.STATUS_FALSE, default=list)

    status = Column(
        EnumTypeDecorator(Status, length=20),
        nullable=constant.STATUS_FALSE,
        default=Status.ACTIVE,
    )

    users = relationship("Users", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")


class Modules(Base, TimestampMixin):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=constant.STATUS_TRUE, index=constant.STATUS_TRUE)

    name = Column(String(100), nullable=constant.STATUS_FALSE)
    slug = Column(
        String(100),
        unique=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
        nullable=constant.STATUS_FALSE,
    )
    description = Column(String(500), nullable=constant.STATUS_TRUE)

    status = Column(
        EnumTypeDecorator(Status, length=20),
        nullable=constant.STATUS_FALSE,
        default=Status.ACTIVE,
    )

    activity_logs = relationship("ActivityLog", back_populates="module")
    role_permissions = relationship("RolePermission", back_populates="module")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=constant.STATUS_TRUE, index=constant.STATUS_TRUE)

    name = Column(
        String(100), nullable=constant.STATUS_FALSE, unique=constant.STATUS_TRUE
    )
    code = Column(
        String(100),
        nullable=constant.STATUS_FALSE,
        unique=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )

    created_at = Column(DateTime, default=func.now(), nullable=constant.STATUS_FALSE)
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=constant.STATUS_FALSE,
    )

    role_permissions = relationship("RolePermission", back_populates="permission")


class RolePermission(Base):
    __tablename__ = "role_module_permissions"

    id = Column(Integer, primary_key=constant.STATUS_TRUE, index=constant.STATUS_TRUE)

    role_id = Column(
        Integer,
        ForeignKey("roles.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    module_id = Column(
        Integer,
        ForeignKey("modules.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )
    permission_id = Column(
        Integer,
        ForeignKey("permissions.id"),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )

    created_at = Column(DateTime, default=func.now(), nullable=constant.STATUS_FALSE)
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=constant.STATUS_FALSE,
    )

    role = relationship("Roles", back_populates="role_permissions")
    module = relationship("Modules", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id = Column(
        BigInteger, primary_key=constant.STATUS_TRUE, index=constant.STATUS_TRUE
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )
    module_id = Column(
        Integer,
        ForeignKey("modules.id"),
        nullable=constant.STATUS_TRUE,
        index=constant.STATUS_TRUE,
    )

    action = Column(
        EnumTypeDecorator(Action, length=20),
        nullable=constant.STATUS_FALSE,
        index=constant.STATUS_TRUE,
    )

    entity_id = Column(
        String(100), nullable=constant.STATUS_TRUE, index=constant.STATUS_TRUE
    )
    description = Column(Text, nullable=constant.STATUS_TRUE)

    activity_metadata = Column(JSON, nullable=constant.STATUS_TRUE)
    ip_address = Column(String(45), nullable=constant.STATUS_TRUE)

    user = relationship("Users", back_populates="activity_logs")
    module = relationship("Modules", back_populates="activity_logs")
