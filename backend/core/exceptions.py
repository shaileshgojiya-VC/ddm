"""
Custom exceptions.
"""


class BaseAPIException(Exception):
    """Base API exception."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(BaseAPIException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationException(BaseAPIException):
    """Validation exception."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class AuthenticationException(BaseAPIException):
    """Authentication exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationException(BaseAPIException):
    """Authorization exception."""

    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, status_code=403)
