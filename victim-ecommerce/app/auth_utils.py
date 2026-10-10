"""JWT helpers for storefront and demo routes."""
import logging
from typing import Optional

import jwt
from fastapi import HTTPException, Request

from app.config import JWT_ALGORITHM, JWT_SECRET, VULN_MODE

logger = logging.getLogger(__name__)


def get_optional_user_id(request: Request) -> Optional[int]:
    """Return user_id from a valid Bearer token, or None if missing/invalid."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        return int(user_id)
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        logger.info("Rejected invalid JWT: %s", exc)
        return None


def require_user_id(request: Request) -> int:
    """Require a valid JWT. Missing or invalid tokens are 401, not user 1."""
    user_id = get_optional_user_id(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def demo_fallback_user_id(request: Request) -> int:
    """
    Identity for endpoints that still participate in the vulnerability demo.

    VULN_MODE=true  → missing/invalid token maps to user 1 (intentional BOLA).
    VULN_MODE=false → same as require_user_id.
    """
    user_id = get_optional_user_id(request)
    if user_id is not None:
        return user_id
    if VULN_MODE:
        return 1
    raise HTTPException(status_code=401, detail="Authentication required")
