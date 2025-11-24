"""
JWT token validation for Layer55 authentication.
"""
import os
import logging
from typing import Dict, Optional
import jwt
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class JWTValidator:
    """Validates JWT tokens issued by Layer55 API"""

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize JWT validator.

        Args:
            secret_key: JWT secret key (if not provided, loads from env)
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY must be set in environment variables")

        self.algorithm = "HS256"
        logger.info("JWT validator initialized successfully")

    def validate_token(self, token: str) -> Dict[str, any]:
        """
        Validate JWT token and extract claims.

        Args:
            token: JWT token string

        Returns:
            Dict containing token claims including user_id

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
            ValueError: Token structure is invalid
        """
        if not token:
            raise ValueError("Token cannot be empty")

        try:
            # Decode and validate token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "require": ["sub", "exp"]
                }
            )

            # Extract user_id from sub claim
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Token missing 'sub' claim with user_id")

            # Log successful validation (without exposing token)
            logger.debug(f"Successfully validated JWT for user_id: {user_id}")

            return {
                "user_id": user_id,
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                "scope": payload.get("scope"),
                "raw_payload": payload
            }

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise
        except jwt.InvalidSignatureError:
            logger.error("JWT token has invalid signature")
            raise
        except jwt.DecodeError:
            logger.error("JWT token decode error")
            raise
        except Exception as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise

    def extract_user_id(self, token: str) -> str:
        """
        Extract user_id from JWT token.

        Args:
            token: JWT token string

        Returns:
            User ID string
        """
        claims = self.validate_token(token)
        return claims["user_id"]


def validate_jwt_token(token: str) -> Dict[str, any]:
    """
    Convenience function to validate JWT token.

    Args:
        token: JWT token string

    Returns:
        Dict containing token claims
    """
    validator = JWTValidator()
    return validator.validate_token(token)
