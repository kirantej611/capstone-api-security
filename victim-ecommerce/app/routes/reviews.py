"""
reviews.py — Product review routes
Endpoints:
  POST /api/products/{product_id}/reviews  — add review (VULN_MODE: stored XSS via unescaped comment)
  GET  /api/products/{product_id}/reviews  — list reviews (reflects stored XSS payloads)
"""
import html
import logging
import jwt
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

from app.database import pool
from app.config import VULN_MODE, JWT_SECRET, JWT_ALGORITHM
from app.models.schemas import ReviewCreate, ReviewOut

logger = logging.getLogger(__name__)
router = APIRouter()


def _extract_user_id(request: Request) -> int:
    """
    Extract user_id from JWT. Returns 1 if missing / invalid.
    Defaulting to user_id=1 without auth is itself an intentional weakness.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("user_id", 1)
        except Exception:
            pass
    return 1


@router.post("/api/products/{product_id}/reviews", status_code=201)
async def add_review(product_id: int, data: ReviewCreate, request: Request):
    """
    Add a review to a product.

    VULN_MODE=true  → comment stored raw in DB without HTML escaping (Stored XSS).
    VULN_MODE=false → comment is HTML-escaped before storage.
    """
    user_id = _extract_user_id(request)

    if VULN_MODE:
        # ── VULNERABLE PATH ────────────────────────────────────────────────────
        # XSS payload stored verbatim:  <script>alert('xss')</script>
        comment = data.comment
    else:
        # ── SAFE PATH ──────────────────────────────────────────────────────────
        comment = html.escape(data.comment)

    async with pool.acquire() as conn:
        # Verify product exists
        exists = await conn.fetchval("SELECT 1 FROM products WHERE id=$1", product_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Product not found")

        row = await conn.fetchrow(
            """INSERT INTO reviews (product_id, user_id, rating, comment)
               VALUES ($1, $2, $3, $4)
               RETURNING id, product_id, user_id, rating, comment, created_at""",
            product_id, user_id, data.rating, comment,
        )

    logger.info(f"Review added to product {product_id} by user {user_id}")
    return ReviewOut(
        id=row["id"],
        product_id=row["product_id"],
        user_id=row["user_id"],
        rating=row["rating"],
        comment=row["comment"],    # returned verbatim — XSS reflected if client renders HTML
        created_at=str(row["created_at"]),
    )


@router.get("/api/products/{product_id}/reviews")
async def get_reviews(product_id: int):
    """
    Get all reviews for a product.
    Stored XSS payloads are returned verbatim in VULN_MODE (no re-escaping on read).
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM reviews WHERE product_id=$1 ORDER BY created_at DESC",
            product_id,
        )
    return [
        ReviewOut(
            id=r["id"],
            product_id=r["product_id"],
            user_id=r["user_id"],
            rating=r["rating"],
            comment=r["comment"],
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]
