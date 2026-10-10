"""
cart.py — Shopping cart routes (PostgreSQL)

Carts persist in cart_items. They are per-process database rows, so they
survive API restarts. They do not sync across independently provisioned
databases.

POST /api/cart/add and GET/DELETE /api/cart require a valid JWT in normal
operation. VULN_MODE still maps missing tokens to user 1 (BOLA demo).
"""
import logging

from fastapi import APIRouter, HTTPException, Request

from app import database
from app.auth_utils import demo_fallback_user_id, require_user_id
from app.config import VULN_MODE
from app.errors import raise_internal_error
from app.models.schemas import CartItem, MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _cart_user_id(request: Request) -> int:
    if VULN_MODE:
        return demo_fallback_user_id(request)
    return require_user_id(request)


@router.post("/api/cart/add", response_model=MessageResponse)
async def add_to_cart(data: CartItem, request: Request):
    user_id = _cart_user_id(request)

    async with database.pool.acquire() as conn:
        try:
            product = await conn.fetchrow(
                "SELECT id, name, price, stock FROM products WHERE id=$1",
                data.item_id,
            )
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {data.item_id} not found")
            existing_qty = await conn.fetchval(
                "SELECT quantity FROM cart_items WHERE user_id=$1 AND product_id=$2",
                user_id,
                data.item_id,
            )
            requested = (existing_qty or 0) + data.qty
            if product["stock"] < requested:
                raise HTTPException(status_code=400, detail="Requested quantity exceeds stock")

            await conn.execute(
                """
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
                """,
                user_id,
                data.item_id,
                data.qty,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise_internal_error(exc, "Could not update cart")

    logger.info("User %s added item %s (qty=%s) to cart", user_id, data.item_id, data.qty)
    return MessageResponse(message=f"Added {data.qty}x '{product['name']}' to cart")


@router.get("/api/cart")
async def view_cart(request: Request):
    user_id = _cart_user_id(request)

    async with database.pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                """
                SELECT c.product_id, c.quantity, p.name, p.price
                FROM cart_items c
                JOIN products p ON p.id = c.product_id
                WHERE c.user_id = $1
                ORDER BY c.id
                """,
                user_id,
            )
        except Exception as exc:
            raise_internal_error(exc, "Could not load cart")

    enriched = []
    total = 0.0
    for row in rows:
        line_total = float(row["price"]) * row["quantity"]
        total += line_total
        enriched.append(
            {
                "item_id": row["product_id"],
                "name": row["name"],
                "qty": row["quantity"],
                "unit_price": float(row["price"]),
                "line_total": round(line_total, 2),
            }
        )
    return {"user_id": user_id, "items": enriched, "total": round(total, 2)}


@router.delete("/api/cart/items/{product_id}", response_model=MessageResponse)
async def remove_cart_item(product_id: int, request: Request):
    user_id = _cart_user_id(request)
    async with database.pool.acquire() as conn:
        try:
            result = await conn.execute(
                "DELETE FROM cart_items WHERE user_id=$1 AND product_id=$2",
                user_id,
                product_id,
            )
        except Exception as exc:
            raise_internal_error(exc, "Could not update cart")
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Item not in cart")
    return MessageResponse(message="Item removed from cart")


@router.delete("/api/cart", response_model=MessageResponse)
async def clear_cart(request: Request):
    user_id = _cart_user_id(request)
    async with database.pool.acquire() as conn:
        try:
            await conn.execute("DELETE FROM cart_items WHERE user_id=$1", user_id)
        except Exception as exc:
            raise_internal_error(exc, "Could not clear cart")
    return MessageResponse(message="Cart cleared")
