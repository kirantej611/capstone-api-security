"""
user.py — User profile route
Endpoint: GET /api/user/profile

Vulnerability (BOLA): if ?user_id= query param is supplied, that user's profile
is returned regardless of who is authenticated — a classic Broken Object Level
Authorization (BOLA / IDOR) flaw used in the security demo.
"""
import logging
import jwt
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request

from app.database import pool
from app.config import JWT_SECRET, JWT_ALGORITHM
from app.models.schemas import ProfileOut

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/user/profile", response_model=ProfileOut)
async def get_profile(
    request: Request,
    user_id: Optional[int] = Query(default=None, description="Target user ID (BOLA vulnerability)"),
):
    """
    Return user profile.

    BOLA: if ?user_id= is provided, that profile is returned without any
    ownership check, so any caller can enumerate any user's details.
    """
    if user_id is None:
        # Try to get from JWT
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user_id = payload.get("user_id", 1)
            except Exception:
                user_id = 1
        else:
            user_id = 1  # Default — BOLA: returns user 1 even without auth

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, email, role, created_at FROM users WHERE id=$1",
            user_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"Profile viewed for user_id={user_id}")
    return ProfileOut(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        role=row["role"],
        created_at=str(row["created_at"]),
    )
