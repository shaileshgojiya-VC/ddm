"""JWT token handler utility."""

import os
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from config.env_config import settings


class JWTHandler:
    """Handle JWT token creation and validation."""

    def __init__(self):
        # Use settings from env_config which has proper defaults and validation
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

        # Validate that required values are set
        if not self.secret_key:
            raise ValueError(
                "JWT_SECRET_KEY is required but not set in environment variables"
            )
        if not self.algorithm:
            raise ValueError(
                "JWT_ALGORITHM is required but not set in environment variables"
            )

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT access token.

        Args:
            data: Data to encode in token (user_id, email, etc.)

        Returns:
            JWT token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token data

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_user_id_from_token(self, token: str) -> str:
        """
        Extract user ID from JWT token.

        Args:
            token: JWT token string

        Returns:
            User ID from token
        """
        payload = self.verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no user_id found",
            )

        return user_id

    def get_user_email_from_token(self, token: str) -> str:
        """
        Extract user email from JWT token.

        Args:
            token: JWT token string

        Returns:
            User email from token
        """
        payload = self.verify_token(token)
        email = payload.get("email")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no email found",
            )

        return email

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token with longer expiration.

        Args:
            data: Data to encode in token (user_id, email, etc.)

        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT refresh token.

        Args:
            token: JWT refresh token string

        Returns:
            Decoded token data

        Raises:
            HTTPException: If token is invalid, expired, or not a refresh token
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify this is a refresh token
            token_type = payload.get("type")
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type: refresh token required",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Global JWT handler instance
jwt_handler = JWTHandler()
