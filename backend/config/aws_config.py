"""
AWS configuration.
"""

import boto3
from config.env_config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def get_s3_client():
    """Get S3 client."""
    return s3_client
