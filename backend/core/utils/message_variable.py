"""
Message variables for responses.
"""

# Success Messages
USER_CREATED = "User created successfully"
USER_UPDATED = "User updated successfully"
USER_UPDATED_SUCCESS = "User updated successfully"
USER_DELETED = "User deleted successfully"
USER_RETRIEVED_SUCCESS = "User retrieved successfully"
USERS_RETRIEVED_SUCCESS = "Users retrieved successfully"
SUPPLIERS_RETRIEVED_SUCCESS = "Suppliers retrieved successfully"
SUPPLIER_RETRIEVED_SUCCESS = "Supplier retrieved successfully"
ROLES_RETRIEVED_SUCCESS = "Roles retrieved successfully"
MODULES_RETRIEVED_SUCCESS = "Modules retrieved successfully"
PASSWORD_CHANGED_SUCCESS = (
    "Password changed successfully. You now have full access to the platform."
)
LOGIN_SUCCESS = "Login successful"
LOGOUT_SUCCESS = "Logout successful"
REFRESH_TOKEN_SUCCESS = "Token refreshed successfully"

# Error Messages
USER_NOT_FOUND = "User not found"
INVALID_CREDENTIALS = "Invalid credentials"
UNAUTHORIZED = "Unauthorized access"
FORBIDDEN = "Forbidden access"
INVALID_EMAIL_OR_PASSWORD = "Invalid email or password"
USER_INACTIVE = "User account is inactive"
USER_ALREADY_EXISTS = "User with this email already exists"
ROLE_NOT_FOUND = "Role not found"
CREATOR_NOT_FOUND = "Creator user not found"
EMAIL_SEND_FAILED = "Failed to send email"
SOMETHING_WENT_WRONG = "Something went wrong, Please try again later!"
DELETE_ACCESS_DENIED = "Access denied"
ONLY_ADMIN_CAN_DELETE = "Only admin users can delete users"
INVALID_CURRENT_PASSWORD = "Current password is incorrect"
PASSWORD_MISMATCH = "New password and confirm password do not match"
PASSWORD_REQUIREMENTS_NOT_MET = "Password must be at least 8 characters long and contain uppercase, lowercase, number, and special character"
INVALID_REFRESH_TOKEN = "Invalid or expired refresh token"

# Info Messages
LOGIN_SUCCESSFUL = "Login successful"
USER_CREATION_EMAIL_SENT = "User created successfully. Temporary password sent to email."
FORGET_PASSWORD_SUCCESS = (
    "Password reset link has been sent to your email address. Please check your inbox."
)

# Email Collection Success Messages
CONNECTOR_CREATED_SUCCESS = "Email connector created successfully"
CONNECTORS_RETRIEVED_SUCCESS = "Email connectors retrieved successfully"
MAILBOX_CREATED_SUCCESS = "Email mailbox created successfully"
MAILBOXES_RETRIEVED_SUCCESS = "Email mailboxes retrieved successfully"
SUBSCRIPTION_CREATED_SUCCESS = "Webhook subscription created successfully"
DELTA_SYNC_SUCCESS = "Delta sync completed successfully"
WEBHOOK_PROCESSED_SUCCESS = "Webhook notification processed successfully"
EMAILS_RETRIEVED_SUCCESS = "Emails retrieved successfully"
SPREADSHEET_SYNC_SUCCESS = "Spreadsheet email sync completed successfully"

# Email Collection Error Messages
CONNECTOR_NOT_FOUND = "Email connector not found"
CONNECTOR_ALREADY_EXISTS = "Email connector already exists for this email"
CONNECTOR_INACTIVE = "Email connector is inactive"
MAILBOX_NOT_FOUND = "Email mailbox not found"
MAILBOX_ALREADY_EXISTS = "Email mailbox already exists for this email"
MAILBOX_INACTIVE = "Email mailbox is inactive"
WEBHOOK_URL_REQUIRED = "Webhook URL is required for subscription creation"

# Request Messages
REQUEST_RETRIEVED_SUCCESS = "Request retrieved successfully"
REQUESTS_RETRIEVED_SUCCESS = "Requests retrieved successfully"
REQUEST_NOT_FOUND = "Request not found"
REQUEST_LIST_SUCCESS = "Requests list retrieved successfully"

# Category Messages
CATEGORIES_RETRIEVED_SUCCESS = "Categories retrieved successfully"

# Product Messages
PRODUCTS_RETRIEVED_SUCCESS = "Products retrieved successfully"
PRODUCT_RETRIEVED_SUCCESS = "Product retrieved successfully"

# Filter Messages
FILTERS_RETRIEVED_SUCCESS = "Filters retrieved successfully"
INVALID_MODULE = "Invalid module name"
