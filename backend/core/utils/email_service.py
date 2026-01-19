"""
Email service utilities.
"""

from pathlib import Path
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.mail_config import get_mail_config
import logging

logger = logging.getLogger(__name__)

mail_config = get_mail_config()


def render_email_template(template_path: str, **kwargs) -> str:
    """
    Render email template with provided variables.

    Args:
        template_path: Path to template file relative to assets/template
        **kwargs: Variables to replace in template

    Returns:
        Rendered HTML string
    """
    base_dir = Path(__file__).parent.parent.parent
    template_file = base_dir / "assets" / "template" / template_path

    if not template_file.exists():
        raise FileNotFoundError(f"Template not found: {template_file}")

    with open(template_file, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Simple template variable replacement
    for key, value in kwargs.items():
        template_content = template_content.replace(f"${key}", str(value))
        template_content = template_content.replace(f"${{{key}}}", str(value))

    return template_content


async def send_email(to: str, subject: str, body: str, html: bool = False):
    """
    Send email using SMTP configuration.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        html: Whether body is HTML format
    """
    #    from loguru import logger

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_config["user"]
    message["To"] = to

    if html:
        part = MIMEText(body, "html")
    else:
        part = MIMEText(body, "plain")

    message.attach(part)

    logger.info(f"Attempting to send email to {to} via {mail_config['host']}:{mail_config['port']}")
    logger.debug(f"SMTP User: {mail_config['user']}")

    try:
        # Port 465 requires SSL from the start, port 587 uses STARTTLS
        # AWS SES and Gmail support both: 465 (SSL) and 587 (STARTTLS)
        port = int(mail_config["port"])
        use_ssl = port == 465
        use_starttls = port == 587 and mail_config["use_tls"]

        # For port 465: use_tls=True (SSL from start)
        # For port 587: use_tls=False (we'll upgrade with starttls() after connect)
        # Set timeout to 15 seconds to prevent hanging on slow/unreachable servers
        smtp = aiosmtplib.SMTP(
            hostname=mail_config["host"], port=port, use_tls=use_ssl, timeout=15.0
        )
        await smtp.connect(timeout=15.0)

        # Use STARTTLS if needed (for port 587) - upgrade connection to TLS
        # Only call starttls() if not already using TLS
        if use_starttls:
            try:
                await smtp.starttls(timeout=15.0)
            except Exception as tls_error:
                # If starttls fails because TLS is already active, that's okay - continue
                error_msg = str(tls_error).lower()
                if "already using tls" in error_msg or "connection already using tls" in error_msg:
                    logger.debug("TLS already active, skipping starttls()")
                else:
                    # Re-raise if it's a different error
                    raise

        # Login - use email_username if available, otherwise fall back to user
        username = mail_config["email_username"]
        if not username:
            raise ValueError(
                "No username found in mail_config. Please set SMTP_USER or EMAIL_USERNAME."
            )

        await smtp.login(username, mail_config["password"], timeout=15.0)
        await smtp.send_message(message, timeout=15.0)
        await smtp.quit(timeout=15.0)
        logger.info(f"Email sent successfully to {to}")
    except Exception as e:
        logger.error(f"SMTP connection error: {e}")
        logger.error(
            f"Host: {mail_config['host']}, Port: {mail_config['port']}, User: {mail_config.get('user') or mail_config.get('email_username')}"
        )
        logger.error(f"Using SSL: {use_ssl}, Using STARTTLS: {use_starttls}")
        logger.error("Note: If port 465 times out, try port 587 with STARTTLS instead")
        raise
