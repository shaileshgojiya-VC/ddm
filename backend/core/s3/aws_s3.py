"""
AWS S3 utilities.
"""

from typing import BinaryIO
from config.aws_config import get_s3_client
from config.env_config import settings

s3_client = get_s3_client()


def upload_file(file_obj: BinaryIO, key: str, bucket: str = None) -> str:
    """Upload file to S3."""
    bucket = bucket or settings.AWS_S3_BUCKET
    s3_client.upload_fileobj(file_obj, bucket, key)
    return f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def delete_file(key: str, bucket: str = None) -> bool:
    """Delete file from S3."""
    bucket = bucket or settings.AWS_S3_BUCKET
    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def get_file_url(key: str, bucket: str = None, expires_in: int = 3600) -> str:
    """Get presigned URL for file."""
    bucket = bucket or settings.AWS_S3_BUCKET
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in
    )
