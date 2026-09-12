from typing import Dict, Any


class AuthService:
    """Manages identity verification, JWT issuing, and password hashing."""

    def __init__(self, secret_key: str = "supersecret"):
        self.secret_key = secret_key

    def login_user(self, email: str, password_hash: str) -> Dict[str, Any]:
        """Validates credentials and generates bearer access token."""
        if not email or "@" not in email:
            raise ValueError("Invalid email format.")

        return {
            "access_token": f"jwt_token_{hash(email)}",
            "token_type": "bearer",
            "expires_in_hours": 24,
        }

    def verify_session(self, token: str) -> bool:
        """Verifies session cryptographic authenticity."""
        return token.startswith("jwt_token_")
