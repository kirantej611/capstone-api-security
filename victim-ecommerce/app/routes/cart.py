"""
cart.py — Shopping cart routes (in-memory store)
Endpoints:
  POST   /api/cart/add  — add item to cart (BOLA: no ownership check)
  GET    /api/cart      — view cart        (BOLA: no ownership check)
  DELETE /api/cart      — clear cart

Vulnerability: cart is keyed by user_id extracted from JWT.
Any caller that omits the token gets user_id=1 — they can inadvertently
(or deliberately) read/modify another user's cart.
"""
import logging
import jwt
from fastapi import APIRouter, HTTPException, Request

from app.database import pool
from app.config import JWT_SECRET, JWT_ALGORITHM
from app.models.schemas import CartItem, MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory cart: { user_id: [ {"item_id": int, "qty": int}, ... ] }
_carts: dict[int, list[dict]] = {}


def _get_user_id(request: Request) -> int:
    """
    Extract user_id from JWT token.
    Defaults to 1 if token is absent or invalid (BOLA weakness).
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("user_id", 1)
        except Exception:
            pass
    return 1  # BOLA: unauthenticated callers share user 1's cart


@router.post("/api/cart/add", response_model=MessageResponse)
async def add_to_cart(data: CartItem, request: Request):
    """Add an item to the cart. No ownership verification (BOLA)."""
    user_id = _get_user_id(request)

    # Verify the product exists in the database
    async with pool.acquire() as conn:
        product = await conn.fetchrow(
            "SELECT id, name, price FROM products WHERE id=$1", data.item_id
        )
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {data.item_id} not found")

    cart = _carts.setdefault(user_id, [])
    for item in cart:
        if item["item_id"] == data.item_id:
            item["qty"] += data.qty
            break
    else:
        cart.append({"item_id": data.item_id, "qty": data.qty})

    logger.info(f"User {user_id} added item {data.item_id} (qty={data.qty}) to cart")
    return MessageResponse(message=f"Added {data.qty}x '{product['name']}' to cart")


@router.get("/api/cart")
async def view_cart(request: Request):
    """
    View cart contents. No ownership verification — any user_id may be supplied (BOLA).
    Enriches in-memory items with live price/name from the database.
    """
    user_id = _get_user_id(request)
    cart = _carts.get(user_id, [])
    if not cart:
        return {"user_id": user_id, "items": [], "total": 0.0}

    enriched = []
    total = 0.0
    async with pool.acquire() as conn:
        for item in cart:
            row = await conn.fetchrow(
                "SELECT id, name, price FROM products WHERE id=$1", item["item_id"]
            )
            if row:
                line_total = float(row["price"]) * item["qty"]
                total += line_total
                enriched.append({
                    "item_id": row["id"],
                    "name": row["name"],
                    "qty": item["qty"],
                    "unit_price": float(row["price"]),
                    "line_total": line_total,
                })

    return {"user_id": user_id, "items": enriched, "total": round(total, 2)}


@router.delete("/api/cart", response_model=MessageResponse)
async def clear_cart(request: Request):
    """Clear the cart for the current user."""
    user_id = _get_user_id(request)
    _carts.pop(user_id, None)
    return MessageResponse(message="Cart cleared")
