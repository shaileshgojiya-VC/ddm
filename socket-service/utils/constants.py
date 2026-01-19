"""
Socket service constants.
"""

# Socket.IO Event Names
EVENT_CONNECT = "connect"
EVENT_DISCONNECT = "disconnect"
EVENT_MESSAGE = "message"
EVENT_GROUP_MESSAGE = "group_message"
EVENT_JOIN_ROOM = "join_room"
EVENT_LEAVE_ROOM = "leave_room"
EVENT_TYPING = "typing"
EVENT_READ_RECEIPT = "read_receipt"
EVENT_DELIVERY_RECEIPT = "delivery_receipt"
EVENT_PRESENCE = "presence"
EVENT_HEARTBEAT = "heartbeat"

# Response Event Names
EVENT_CONNECTION_RESPONSE = "connection_response"
EVENT_MESSAGE_RESPONSE = "message_response"
EVENT_GROUP_MESSAGE_RESPONSE = "group_message_response"
EVENT_TYPING_RESPONSE = "typing_response"
EVENT_READ_RECEIPT_RESPONSE = "read_receipt_response"
EVENT_PRESENCE_RESPONSE = "presence_response"
EVENT_ERROR = "error"

# Room Prefixes
ROOM_PREFIX = "room_"
GROUP_ROOM_PREFIX = "group_"
USER_ROOM_PREFIX = "user_"

# Redis Pub/Sub Channels
REDIS_CHANNEL_ROOM_PREFIX = "room:"
REDIS_CHANNEL_USER_PREFIX = "user:"
REDIS_CHANNEL_RECEIPT_PREFIX = "receipt:"
REDIS_CHANNEL_PRESENCE_PREFIX = "presence:"

# Message Types
MESSAGE_TYPE_TEXT = "text"
MESSAGE_TYPE_IMAGE = "image"
MESSAGE_TYPE_VIDEO = "video"
MESSAGE_TYPE_FILE = "file"
MESSAGE_TYPE_AUDIO = "audio"

VALID_MESSAGE_TYPES = [
    MESSAGE_TYPE_TEXT,
    MESSAGE_TYPE_IMAGE,
    MESSAGE_TYPE_VIDEO,
    MESSAGE_TYPE_FILE,
    MESSAGE_TYPE_AUDIO,
]

# Connection Limits
MAX_CONNECTIONS_PER_USER = 5
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ATTACHMENT_SIZE = 100 * 1024 * 1024  # 100MB
HEARTBEAT_INTERVAL = 30  # seconds
CONNECTION_TIMEOUT = 60  # seconds

# Rate Limiting
MESSAGE_RATE_LIMIT = 100  # messages per minute per user
CONNECTION_RATE_LIMIT = 10  # connections per minute per IP

# File Type Validation
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/avi", "video/mov", "video/wmv", "video/flv"]
ALLOWED_FILE_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
    "text/csv",
]
ALLOWED_AUDIO_TYPES = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp3"]

# Status Constants
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_CONNECTED = "connected"
STATUS_DISCONNECTED = "disconnected"
STATUS_ONLINE = "online"
STATUS_OFFLINE = "offline"
STATUS_TYPING = "typing"
STATUS_STOPPED_TYPING = "stopped_typing"

# UUID Format Validation
UUID_LENGTH = 36
UUID_HYPHEN_COUNT = 4

