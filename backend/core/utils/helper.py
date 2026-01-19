"""
Helper utilities.
"""

from datetime import datetime

import hashlib
import json
import secrets
from typing import Any, Dict, Optional
import uuid
import bcrypt

def generate_random_string(length: int = 32) -> str:
    """Generate random string."""
    return secrets.token_urlsafe(length)


def hash_string(text: str) -> str:
    """Hash a string."""
    return hashlib.sha256(text.encode()).hexdigest()


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize dictionary by removing None values."""
    return {k: v for k, v in data.items() if v is not None}


def generate_uuid():
    """Generate UUID string."""
    return str(uuid.uuid4())


def generate_temporary_password(length: int = 12) -> str:
    """
    Generate a secure temporary password.

    Args:
        length: Length of the password (default: 12)

    Returns:
        Random secure password string
    """
    import string

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class PasswordUtils:
    """This class is used to manage password management"""

    def __init__(self):
        # Using bcrypt directly instead of passlib for better compatibility
        pass

    def hash_password(self, password: str) -> str:
        """
        This function is used to hash password
        Arguments:
            password(str) : password argument of string format.

        Returns:
            Hash of the password
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        This function is used to verify password
        Arguments:
            plain_password(str) : plain password
            hashed_password(str) : hashed password

        Returns:
            Boolean value indicating if password matches
        """
        try:
            # Verify password using bcrypt
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception:
            return False

class TypeCoercion:
    """This class is used to coerce types"""

    @staticmethod
    def coerce_str(value: Any, default: Optional[str] = None) -> Optional[str]:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            return value.strip() if value.strip() else default
        return str(value) if value else default

    @staticmethod
    def coerce_int(value: Any, default: Optional[int] = None) -> Optional[int]:
        if value is None or value == "":
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(float(value)) if value.strip() else default
            except (ValueError, AttributeError):
                return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def coerce_float(value: Any, default: Optional[float] = None) -> Optional[float]:
        if value is None or value == "":
            return default
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value) if value.strip() else default
            except (ValueError, AttributeError):
                return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def coerce_bool(value: Any, default: bool = False) -> bool:
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            upper = value.upper().strip()
            if upper in ("Y", "YES", "1", "TRUE", "T"):
                return True
            if upper in ("N", "NO", "0", "FALSE", "F", ""):
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    @staticmethod
    def coerce_datetime(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
        if value is None or value == "":
            return default
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Try parsing ISO format with timezone
                if "+" in value or value.endswith("Z"):
                    clean_value = value.split("+")[0].split("Z")[0]
                    if "." in clean_value:
                        clean_value = clean_value.split(".")[0]
                    return datetime.fromisoformat(clean_value)
                return datetime.fromisoformat(value)
            except (ValueError, AttributeError):
                return default
        return default


    @staticmethod
    def coerce_list(value: Any, default: Optional[list] = None) -> list:
        """
        Coerce value to list. Accepts JSON strings, lists, or returns default/empty list.
        """
        if value is None:
            return default if default is not None else []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else (default if default is not None else [])
            except Exception:
                return default if default is not None else []
        return [value] if value else (default if default is not None else [])