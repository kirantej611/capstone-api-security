"""
reviews.py — Product review routes
Endpoints:
  POST /api/products/{product_id}/reviews  — add review (VULN_MODE: stored XSS)
  GET  /api/products/{product_id}/reviews  — list reviews
"""
import html
import logging

from fastapi import APIRouter, HTTPException, Request

from app import database
from app.auth_utils import demo_fallback_user_id, require_user_id
from app.config import VULN_MODE
from app.errors import raise_internal_error
from app.models.schemas import ReviewCreate, ReviewOut

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/products/{product_id}/reviews", status_code=201)
async def add_review(product_id: int, data: ReviewCreate, request: Request):
    """
    Add a review to a product.

    VULN_MODE=true  → anonymous posts allowed (user 1) and comment stored raw.
    VULN_MODE=false → authentication required and comment is HTML-escaped.
    """
    user_id = demo_fallback_user_id(request) if VULN_MODE else require_user_id(request)
    comment = data.comment if VULN_MODE else html.escape(data.comment)

    async with database.pool.acquire() as conn:
        try:
            exists = await conn.fetchval("SELECT 1 FROM products WHERE id=$1", product_id)
            if not exists:
                raise HTTPException(status_code=404, detail="Product not found")

            row = await conn.fetchrow(
                """INSERT INTO reviews (product_id, user_id, rating, comment)
                   VALUES ($1, $2, $3, $4)
                   RETURNING id, product_id, user_id, rating, comment, created_at""",
                product_id,
                user_id,
                data.rating,
                comment,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise_internal_error(exc, "Could not save review")

    logger.info("Review added to product %s by user %s", product_id, user_id)
    return ReviewOut(
        id=row["id"],
        product_id=row["product_id"],
        user_id=row["user_id"],
        rating=row["rating"],
        comment=row["comment"],
        created_at=str(row["created_at"]),
    )


@router.get("/api/products/{product_id}/reviews")
async def get_reviews(product_id: int):
    async with database.pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                "SELECT * FROM reviews WHERE product_id=$1 ORDER BY created_at DESC",
                product_id,
            )
        except Exception as exc:
            raise_internal_error(exc, "Could not load reviews")
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
