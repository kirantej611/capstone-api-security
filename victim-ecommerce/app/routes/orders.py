"""
orders.py — Order / checkout routes
Endpoints:
  POST /api/checkout          — place an order (transactional)
  GET  /api/orders            — list current user's orders
  GET  /api/orders/{order_id} — view an order (VULN_MODE: BOLA, no auth check)
"""
import logging

from fastapi import APIRouter, HTTPException, Request

from app import database
from app.auth_utils import require_user_id
from app.config import VULN_MODE
from app.errors import raise_internal_error
from app.models.schemas import CheckoutRequest, OrderItemOut, OrderOut

logger = logging.getLogger(__name__)
router = APIRouter()


def _order_from_row(row, items) -> OrderOut:
    return OrderOut(
        id=row["id"],
        user_id=row["user_id"],
        total=float(row["total"]),
        status=row["status"],
        shipping_address=row["shipping_address"],
        items=items,
        created_at=str(row["created_at"]),
    )


@router.post("/api/checkout", status_code=201)
async def checkout(data: CheckoutRequest, request: Request):
    """Create an order and its items in one transaction; clear cart only after commit."""
    user_id = require_user_id(request)

    async with database.pool.acquire() as conn:
        try:
            async with conn.transaction():
                cart_rows = await conn.fetch(
                    """
                    SELECT c.product_id, c.quantity, p.price, p.name, p.stock
                    FROM cart_items c
                    JOIN products p ON p.id = c.product_id
                    WHERE c.user_id = $1
                    FOR UPDATE
                    """,
                    user_id,
                )
                if not cart_rows:
                    raise HTTPException(status_code=400, detail="Cart is empty")

                items_with_prices = []
                total = 0.0
                for item in cart_rows:
                    if item["stock"] < item["quantity"]:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient stock for {item['name']}",
                        )
                    line_total = float(item["price"]) * item["quantity"]
                    total += line_total
                    items_with_prices.append(
                        {
                            "product_id": item["product_id"],
                            "quantity": item["quantity"],
                            "price": float(item["price"]),
                            "name": item["name"],
                        }
                    )

                order_row = await conn.fetchrow(
                    """INSERT INTO orders (user_id, total, status, shipping_address)
                       VALUES ($1, $2, 'pending', $3)
                       RETURNING id, user_id, total, status, shipping_address, created_at""",
                    user_id,
                    round(total, 2),
                    data.shipping_address,
                )
                order_id = order_row["id"]

                for item in items_with_prices:
                    await conn.execute(
                        """INSERT INTO order_items (order_id, product_id, quantity, price)
                           VALUES ($1, $2, $3, $4)""",
                        order_id,
                        item["product_id"],
                        item["quantity"],
                        item["price"],
                    )
                    await conn.execute(
                        "UPDATE products SET stock = stock - $1 WHERE id=$2",
                        item["quantity"],
                        item["product_id"],
                    )

                await conn.execute("DELETE FROM cart_items WHERE user_id=$1", user_id)
        except HTTPException:
            raise
        except Exception as exc:
            raise_internal_error(exc, "Checkout failed")

    logger.info("Order %s placed by user %s, total=$%.2f", order_id, user_id, total)
    return _order_from_row(
        order_row,
        [OrderItemOut(**item) for item in items_with_prices],
    )


@router.get("/api/orders")
async def list_orders(request: Request):
    user_id = require_user_id(request)
    async with database.pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                """SELECT id, user_id, total, status, shipping_address, created_at
                   FROM orders WHERE user_id=$1 ORDER BY id DESC""",
                user_id,
            )
            result = []
            for row in rows:
                item_rows = await conn.fetch(
                    """SELECT oi.product_id, oi.quantity, oi.price, p.name
                       FROM order_items oi
                       JOIN products p ON p.id = oi.product_id
                       WHERE oi.order_id=$1""",
                    row["id"],
                )
                items = [
                    OrderItemOut(
                        product_id=i["product_id"],
                        quantity=i["quantity"],
                        price=float(i["price"]),
                        name=i["name"],
                    )
                    for i in item_rows
                ]
                result.append(_order_from_row(row, items))
        except Exception as exc:
            raise_internal_error(exc, "Could not load orders")
    return result


@router.get("/api/orders/{order_id}")
async def get_order(order_id: str, request: Request):
    """
    Get order details.

    VULN_MODE=true  → no authentication check; any caller can view any order (BOLA).
    VULN_MODE=false → verifies the requesting user owns the order.
    """
    async with database.pool.acquire() as conn:
        try:
            if VULN_MODE:
                query = f"SELECT * FROM orders WHERE id = {order_id}"
                row = await conn.fetchrow(query)
            else:
                user_id = require_user_id(request)
                row = await conn.fetchrow(
                    "SELECT * FROM orders WHERE id=$1 AND user_id=$2",
                    int(order_id),
                    user_id,
                )
        except HTTPException:
            raise
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid order ID")
        except Exception as exc:
            logger.warning("Order query error: %s", exc)
            if VULN_MODE:
                raise HTTPException(status_code=400, detail=f"Query error: {exc}")
            raise HTTPException(status_code=400, detail="Invalid order request")

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        try:
            items_rows = await conn.fetch(
                """SELECT oi.product_id, oi.quantity, oi.price, p.name
                   FROM order_items oi
                   JOIN products p ON p.id = oi.product_id
                   WHERE oi.order_id=$1""",
                row["id"],
            )
        except Exception as exc:
            raise_internal_error(exc, "Could not load order items")

    items = [
        OrderItemOut(
            product_id=i["product_id"],
            quantity=i["quantity"],
            price=float(i["price"]),
            name=i["name"],
        )
        for i in items_rows
    ]
    return _order_from_row(row, items)
