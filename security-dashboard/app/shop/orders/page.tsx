'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Order, ShopApiError, getShopUser, listOrders } from '../../../lib/shopApi';

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!getShopUser()) {
        setError('Sign in to view your orders.');
        setLoading(false);
        return;
      }
      try {
        setOrders(await listOrders());
      } catch (err) {
        setError(err instanceof ShopApiError ? err.message : 'Could not load orders');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div>
      <h1>Orders</h1>
      {error && <div className="shop-alert error">{error}</div>}
      {loading && <div className="shop-loading">Loading orders…</div>}
      {!loading && !error && orders.length === 0 && <div className="shop-empty">No orders yet.</div>}
      <div className="review-list">
        {orders.map((order) => (
          <article key={order.id} className="review-item">
            <strong>Order #{order.id}</strong>
            <p>
              {order.status} · ${order.total.toFixed(2)}
            </p>
            <Link href={`/shop/orders/${order.id}`}>View order</Link>
          </article>
        ))}
      </div>
    </div>
  );
}
