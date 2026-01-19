"""
Validation utilities.
"""

from typing import Any
from pydantic import ValidationError


def validate_data(schema_class: Any, data: dict) -> tuple[bool, Any, str]:
    """Validate data against a Pydantic schema."""
    try:
        validated_data = schema_class(**data)
        return True, validated_data, ""
    except ValidationError as e:
        error_message = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        return False, None, error_message
