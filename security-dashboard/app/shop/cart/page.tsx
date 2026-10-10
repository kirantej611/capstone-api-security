'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  CartResponse,
  ShopApiError,
  getCart,
  getShopUser,
  removeCartItem,
} from '../../../lib/shopApi';

export default function CartPage() {
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError(null);
    if (!getShopUser()) {
      setCart(null);
      setError('Sign in to view your cart.');
      setLoading(false);
      return;
    }
    try {
      setCart(await getCart());
    } catch (err) {
      setCart(null);
      setError(err instanceof ShopApiError ? err.message : 'Could not load cart');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const removeItem = async (id: number) => {
    setError(null);
    try {
      await removeCartItem(id);
      await load();
    } catch (err) {
      setError(err instanceof ShopApiError ? err.message : 'Could not update cart');
    }
  };

  return (
    <div>
      <h1>Cart</h1>
      {error && <div className="shop-alert error">{error}</div>}
      {loading && <div className="shop-loading">Loading cart…</div>}
      {!loading && cart && cart.items.length === 0 && (
        <div className="shop-empty">Your cart is empty.</div>
      )}
      {cart && cart.items.length > 0 && (
        <>
          <table className="shop-table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Qty</th>
                <th>Price</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {cart.items.map((item) => (
                <tr key={item.item_id}>
                  <td>{item.name}</td>
                  <td>{item.qty}</td>
                  <td>${item.line_total.toFixed(2)}</td>
                  <td>
                    <button className="shop-btn-secondary" type="button" onClick={() => removeItem(item.item_id)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ margin: '1rem 0' }}>
            <strong>Total: ${cart.total.toFixed(2)}</strong>
          </p>
          <Link className="shop-btn" href="/shop/checkout" style={{ display: 'inline-block', textDecoration: 'none' }}>
            Checkout
          </Link>
        </>
      )}
    </div>
  );
}
