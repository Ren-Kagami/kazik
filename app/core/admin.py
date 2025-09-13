"""
Admin authentication and management for slot machine game.
"""

import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from app.core.config import logger

# Admin configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Default admin password hash (password: "admin123" - change in production!)
DEFAULT_ADMIN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"


class AdminManager:
    """
    Handles admin authentication and authorization.
    Provides JWT token-based authentication for admin operations.
    """

    def __init__(self) -> None:
        """Initialize admin manager with configuration."""
        self.admin_username = ADMIN_USERNAME
        self.admin_password_hash = ADMIN_PASSWORD_HASH or DEFAULT_ADMIN_HASH
        self.jwt_secret = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        self.expiration_hours = JWT_EXPIRATION_HOURS

        # Warn about default credentials
        if self.admin_password_hash == DEFAULT_ADMIN_HASH:
            logger.warning(
                "Using default admin password! Change ADMIN_PASSWORD_HASH in production!"
            )

        logger.info("Admin manager initialized")

    def hash_password(self, password: str) -> str:
        """
        Create SHA-256 hash of password with salt.

        Args:
            password: Plain text password

        Returns:
            Hexadecimal hash string
        """
        salt = "slot_machine_admin_salt_2025"  # Static salt for simplicity
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def verify_credentials(self, username: str, password: str) -> bool:
        """
        Verify admin login credentials.

        Args:
            username: Provided username
            password: Provided password

        Returns:
            True if credentials are valid
        """
        try:
            if username != self.admin_username:
                logger.warning(f"Invalid admin username attempt: {username}")
                return False

            password_hash = self.hash_password(password)
            if password_hash != self.admin_password_hash:
                logger.warning(f"Invalid admin password attempt for user: {username}")
                return False

            logger.info(f"Successful admin login: {username}")
            return True

        except Exception as e:
            logger.error(f"Error verifying admin credentials: {e}")
            return False

    def generate_token(self, username: str) -> Dict[str, Any]:
        """
        Generate JWT access token for admin user.

        Args:
            username: Admin username

        Returns:
            Dictionary with token data
        """
        try:
            expires_at = datetime.utcnow() + timedelta(hours=self.expiration_hours)

            payload = {
                "username": username,
                "role": "admin",
                "exp": expires_at.timestamp(),
                "iat": datetime.utcnow().timestamp(),
                "iss": "slot-machine-api"
            }

            token = jwt.encode(
                payload,
                self.jwt_secret,
                algorithm=self.jwt_algorithm
            )

            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": int(self.expiration_hours * 3600),
                "expires_at": expires_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating admin token: {e}")
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )

            # Verify token hasn't expired
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                logger.warning("Expired admin token")
                return None

            # Verify role
            if payload.get("role") != "admin":
                logger.warning(f"Invalid role in token: {payload.get('role')}")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Admin token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid admin token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying admin token: {e}")
            return None

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Perform admin login and return token if successful.

        Args:
            username: Admin username
            password: Admin password

        Returns:
            Token data if login successful, None otherwise
        """
        try:
            if not self.verify_credentials(username, password):
                return None

            return self.generate_token(username)

        except Exception as e:
            logger.error(f"Error during admin login: {e}")
            return None

    def logout(self, token: str) -> bool:
        """
        Logout admin (token blacklisting would be implemented here in production).

        Args:
            token: Token to invalidate

        Returns:
            True if logout successful
        """
        try:
            # In a production system, you would add the token to a blacklist
            # For simplicity, we just verify the token is valid
            payload = self.verify_token(token)
            if payload:
                logger.info(f"Admin logout: {payload.get('username')}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error during admin logout: {e}")
            return False

    def get_admin_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get admin user information from token.

        Args:
            token: Valid JWT token

        Returns:
            Admin user information
        """
        try:
            payload = self.verify_token(token)
            if not payload:
                return None

            return {
                "username": payload.get("username"),
                "role": payload.get("role"),
                "token_issued_at": datetime.fromtimestamp(payload.get("iat", 0)).isoformat(),
                "token_expires_at": datetime.fromtimestamp(payload.get("exp", 0)).isoformat(),
                "permissions": [
                    "view_sessions",
                    "modify_probability",
                    "view_analytics",
                    "delete_sessions",
                    "system_settings"
                ]
            }

        except Exception as e:
            logger.error(f"Error getting admin info: {e}")
            return None

    def change_password(self, current_password: str, new_password: str) -> bool:
        """
        Change admin password (would update database/config in production).

        Args:
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully
        """
        try:
            # Verify current password
            if not self.verify_credentials(self.admin_username, current_password):
                logger.warning("Invalid current password for password change")
                return False

            # Validate new password strength
            if len(new_password) < 8:
                logger.warning("New password too short")
                return False

            # Generate new hash
            new_hash = self.hash_password(new_password)

            # In production, you would update the database/environment
            # For now, just log the action
            logger.info("Admin password change requested (not implemented in demo)")
            logger.info(f"New password hash would be: {new_hash}")

            return True

        except Exception as e:
            logger.error(f"Error changing admin password: {e}")
            return False

    @staticmethod
    def generate_password_hash(password: str) -> str:
        """
        Utility method to generate password hash for configuration.

        Args:
            password: Password to hash

        Returns:
            Hash string for use in configuration
        """
        salt = "slot_machine_admin_salt_2025"
        return hashlib.sha256((password + salt).encode()).hexdigest()


def create_admin_user() -> None:
    """
    Utility function to create admin user hash.
    Run this script to generate password hash for environment variable.
    """
    import getpass

    print("Admin User Setup")
    print("================")

    username = input("Enter admin username (default: admin): ").strip() or "admin"
    password = getpass.getpass("Enter admin password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords don't match!")
        return

    if len(password) < 8:
        print("Password must be at least 8 characters long!")
        return

    admin_manager = AdminManager()
    password_hash = admin_manager.generate_password_hash(password)

    print("\nAdmin user configuration:")
    print(f"ADMIN_USERNAME={username}")
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print("\nAdd these to your environment variables or .env file")


if __name__ == "__main__":
    create_admin_user()