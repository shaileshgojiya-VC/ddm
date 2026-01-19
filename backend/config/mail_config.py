"""
Email configuration.
"""

from config.env_config import settings


def get_mail_config():
    """Get email configuration."""
    return {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "user": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "use_tls": settings.SMTP_USE_TLS,
        "email_username": settings.EMAIL_USERNAME,
        "from_email": settings.FROM_EMAIL,
    }
