"""
products.py — Product catalogue routes
Endpoints:
  GET /api/products           — list (safe, paginated)
  GET /api/products/{id}      — detail (VULN_MODE: SQLi via path param)
  GET /api/search?q=          — search  (VULN_MODE: SQLi + reflected XSS)
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app import database
from app.config import VULN_MODE
from app.errors import raise_internal_error
from app.models.schemas import ProductOut

logger = logging.getLogger(__name__)
router = APIRouter()


def _row_to_product(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "price": float(row["price"]),
        "image_url": row["image_url"],
        "category": row["category"],
        "stock": row["stock"],
    }


@router.get("/api/products")
async def list_products(
    category: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List all products with optional category filter and pagination (always safe)."""
    offset = (page - 1) * limit
    async with database.pool.acquire() as conn:
        try:
            if category:
                rows = await conn.fetch(
                    "SELECT * FROM products WHERE category=$1 ORDER BY id LIMIT $2 OFFSET $3",
                    category, limit, offset,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM products ORDER BY id LIMIT $1 OFFSET $2",
                    limit, offset,
                )
        except Exception as exc:
            raise_internal_error(exc, "Could not load products")
    return [_row_to_product(r) for r in rows]


@router.get("/api/categories")
async def list_categories():
    async with database.pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                "SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category"
            )
        except Exception as exc:
            raise_internal_error(exc, "Could not load categories")
    return [r["category"] for r in rows]


@router.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """
    Get product by ID.

    VULN_MODE=true  → product_id injected raw into SQL (SQLi target).
    VULN_MODE=false → cast to int and use parameterized query.
    """
    async with database.pool.acquire() as conn:
        try:
            if VULN_MODE:
                # ── VULNERABLE PATH ────────────────────────────────────────────
                # e.g. product_id = "1 UNION SELECT id,username,password,email,role,NULL,NULL FROM users--"
                query = f"SELECT * FROM products WHERE id = {product_id}"
                row = await conn.fetchrow(query)
            else:
                # ── SAFE PATH ──────────────────────────────────────────────────
                row = await conn.fetchrow(
                    "SELECT * FROM products WHERE id = $1", int(product_id)
                )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid product ID")
        except Exception as e:
            logger.warning("Product query error: %s", e)
            if VULN_MODE:
                raise HTTPException(status_code=400, detail=f"Query error: {e}")
            raise HTTPException(status_code=400, detail="Invalid product request")

        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        return _row_to_product(row)


@router.get("/api/search")
async def search_products(q: str = Query(..., description="Search query")):
    """
    Search products by name or description.

    VULN_MODE=true  → raw f-string SQL + search term reflected unescaped in response (SQLi + XSS).
    VULN_MODE=false → parameterized query + escaped reflection.
    """
    async with database.pool.acquire() as conn:
        try:
            if VULN_MODE:
                # ── VULNERABLE PATH ────────────────────────────────────────────
                query = f"SELECT * FROM products WHERE name ILIKE '%{q}%' OR description ILIKE '%{q}%'"
                rows = await conn.fetch(query)
                # Return q unescaped (reflected XSS if client renders as HTML)
                reflected_q = q
            else:
                # ── SAFE PATH ──────────────────────────────────────────────────
                rows = await conn.fetch(
                    "SELECT * FROM products WHERE name ILIKE $1 OR description ILIKE $1",
                    f"%{q}%",
                )
                import html
                reflected_q = html.escape(q)
        except Exception as e:
            logger.warning("Search query error: %s", e)
            if VULN_MODE:
                raise HTTPException(status_code=400, detail=f"Query error: {e}")
            raise HTTPException(status_code=400, detail="Search failed")

    products = [_row_to_product(r) for r in rows]
    return {"query": reflected_q, "results": products, "count": len(products)}
