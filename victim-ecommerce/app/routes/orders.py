"""
orders.py — Order / checkout routes
Endpoints:
  POST /api/checkout         — place an order (no rate limiting)
  GET  /api/orders/{order_id} — view an order (VULN_MODE: BOLA, no auth check)
"""
import logging
import jwt
from fastapi import APIRouter, HTTPException, Request

from app.database import pool
from app.config import VULN_MODE, JWT_SECRET, JWT_ALGORITHM
from app.models.schemas import CheckoutRequest, OrderOut, OrderItemOut, MessageResponse
from app.routes.cart import _carts

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("user_id", 1)
        except Exception:
            pass
    return 1


@router.post("/api/checkout", status_code=201)
async def checkout(data: CheckoutRequest, request: Request):
    """
    Place an order from the current cart.
    No rate limiting applied — rapid requests are all accepted (intentional weakness).
    """
    user_id = _get_user_id(request)
    cart = _carts.get(user_id, [])
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    async with pool.acquire() as conn:
        # Fetch product prices
        items_with_prices = []
        total = 0.0
        for item in cart:
            row = await conn.fetchrow(
                "SELECT id, price FROM products WHERE id=$1", item["item_id"]
            )
            if row:
                line = {"product_id": row["id"], "quantity": item["qty"], "price": float(row["price"])}
                items_with_prices.append(line)
                total += float(row["price"]) * item["qty"]

        if not items_with_prices:
            raise HTTPException(status_code=400, detail="No valid products in cart")

        # Create order
        order_row = await conn.fetchrow(
            """INSERT INTO orders (user_id, total, status, shipping_address)
               VALUES ($1, $2, 'pending', $3) RETURNING id, created_at""",
            user_id, round(total, 2), data.shipping_address,
        )
        order_id = order_row["id"]

        # Create order items
        for item in items_with_prices:
            await conn.execute(
                """INSERT INTO order_items (order_id, product_id, quantity, price)
                   VALUES ($1, $2, $3, $4)""",
                order_id, item["product_id"], item["quantity"], item["price"],
            )

    # Clear the cart after successful checkout
    _carts.pop(user_id, None)
    logger.info(f"Order {order_id} placed by user {user_id}, total=${total:.2f}")

    return OrderOut(
        id=order_id,
        user_id=user_id,
        total=round(total, 2),
        status="pending",
        shipping_address=data.shipping_address,
        items=[OrderItemOut(**i) for i in items_with_prices],
        created_at=str(order_row["created_at"]),
    )


@router.get("/api/orders/{order_id}")
async def get_order(order_id: str, request: Request):
    """
    Get order details.

    VULN_MODE=true  → no authentication check; any caller can view any order (BOLA).
    VULN_MODE=false → verifies the requesting user owns the order.
    """
    async with pool.acquire() as conn:
        try:
            if VULN_MODE:
                # ── VULNERABLE PATH ────────────────────────────────────────────
                # No ownership verification — any user can read any order
                query = f"SELECT * FROM orders WHERE id = {order_id}"
                row = await conn.fetchrow(query)
            else:
                # ── SAFE PATH ──────────────────────────────────────────────────
                user_id = _get_user_id(request)
                row = await conn.fetchrow(
                    "SELECT * FROM orders WHERE id=$1 AND user_id=$2",
                    int(order_id), user_id,
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Query error: {e}")

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        items_rows = await conn.fetch(
            "SELECT product_id, quantity, price FROM order_items WHERE order_id=$1",
            row["id"],
        )

    return OrderOut(
        id=row["id"],
        user_id=row["user_id"],
        total=float(row["total"]),
        status=row["status"],
        shipping_address=row["shipping_address"],
        items=[OrderItemOut(product_id=i["product_id"], quantity=i["quantity"], price=float(i["price"]))
               for i in items_rows],
        created_at=str(row["created_at"]),
    )
