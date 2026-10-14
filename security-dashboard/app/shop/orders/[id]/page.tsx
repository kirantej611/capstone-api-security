'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Order, ShopApiError, getOrder, getShopUser } from '../../../../lib/shopApi';
import { formatInr, formatIstTimestamp } from '../../../../lib/formatters';

export default function OrderDetailPage() {
  const params = useParams<{ id: string }>();
  const orderId = Number(params.id);
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!getShopUser()) {
        setError('Sign in to view this order.');
        setLoading(false);
        return;
      }
      try {
        setOrder(await getOrder(orderId));
      } catch (err) {
        setError(err instanceof ShopApiError ? err.message : 'Could not load order');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [orderId]);

  if (loading) return <div className="shop-loading">Loading order…</div>;
  if (error) return <div className="shop-alert error">{error}</div>;
  if (!order) return <div className="shop-empty">Order not found.</div>;

  return (
    <div>
      <h1>Order #{order.id}</h1>
      <p>Status: {order.status}</p>
      <p>Placed: {formatIstTimestamp(order.created_at)}</p>
      <p>Ship to: {order.shipping_address}</p>
      <table className="shop-table" style={{ marginTop: '1rem' }}>
        <thead>
          <tr>
            <th>Item</th>
            <th>Qty</th>
            <th>Price</th>
          </tr>
        </thead>
        <tbody>
          {order.items.map((item) => (
            <tr key={`${item.product_id}-${item.quantity}`}>
              <td>{item.name || `Product ${item.product_id}`}</td>
              <td>{item.quantity}</td>
              <td>{formatInr(item.price)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ marginTop: '1rem' }}>
        <strong>Total: {formatInr(order.total)}</strong>
      </p>
    </div>
  );
}
