"""
Constant variables.
"""

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_500_INTERNAL_SERVER_ERROR = 500

# Common Messages
SUCCESS_MESSAGE = "Operation successful"
ERROR_MESSAGE = "An error occurred"
NOT_FOUND_MESSAGE = "Resource not found"
VALIDATION_ERROR_MESSAGE = "Validation error"

# Status Constants
STATUS_NULL = {}
STATUS_SUCCESS = "success"
STATUS_FAIL = "fail"
STATUS_TRUE = True
STATUS_FALSE = False

# Status Constants
STATUS_NULL = {}
STATUS_SUCCESS = "success"
STATUS_FAIL = "fail"
STATUS_TRUE = True
STATUS_FALSE = False

# API Prefixes
API_V1_PREFIX = "/v1"

# Email Templates
ADMIN_USER_INVITE_HTML_FILE = "emails/admin_user_invite.html"
NEW_USER_SUBJECT = "Welcome to Admin Portal - Your Account Details"

# User attributes
USER_EMAIL_MAX_LENGTH = 255
USER_USERNAME_MAX_LENGTH = 100
USER_PASSWORD_MIN_LENGTH = 8

# Profile attributes
PROFILE_NAME_MAX_LENGTH = 255
PROFILE_PHONE_MIN_LENGTH = 10
PROFILE_PHONE_MAX_LENGTH = 20
PROFILE_LOCATION_MAX_LENGTH = 255
PROFILE_IMAGE_MAX_SIZE = 10 * 1024 * 1024  # 10MB in bytes
PROFILE_IMAGE_ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
PROFILE_FIELDS_ALLOWED_FOR_UPDATE = ["name", "phone_number", "location", "profile_image_url"]
PROFILE_FIELDS_RESTRICTED = ["role_id", "status", "email", "hashed_password", "parent_user_id", "created_by", "bitrix_id"]
