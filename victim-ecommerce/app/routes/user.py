"""
user.py — User profile route
Endpoint: GET /api/user/profile

VULN_MODE BOLA: if ?user_id= is supplied, that profile is returned without
ownership checks. Safe mode ignores the query parameter and requires a JWT.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from app import database
from app.auth_utils import require_user_id
from app.config import VULN_MODE
from app.errors import raise_internal_error
from app.models.schemas import ProfileOut

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/user/profile", response_model=ProfileOut)
async def get_profile(
    request: Request,
    user_id: Optional[int] = Query(default=None, description="Target user ID (BOLA, VULN_MODE only)"),
):
    if VULN_MODE and user_id is not None:
        target_id = user_id
    else:
        target_id = require_user_id(request)

    async with database.pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "SELECT id, username, email, role, created_at FROM users WHERE id=$1",
                target_id,
            )
        except Exception as exc:
            raise_internal_error(exc, "Could not load profile")

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info("Profile viewed for user_id=%s", target_id)
    return ProfileOut(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        role=row["role"],
        created_at=str(row["created_at"]),
    )
