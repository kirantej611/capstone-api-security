'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShopApiError, checkout, getShopUser } from '../../../lib/shopApi';

export default function CheckoutPage() {
  const router = useRouter();
  const [address, setAddress] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!getShopUser()) {
      setError('Sign in to check out.');
      return;
    }
    setPending(true);
    try {
      const order = await checkout(address);
      router.push(`/shop/orders/${order.id}`);
    } catch (err) {
      setError(err instanceof ShopApiError ? err.message : 'Checkout failed');
    } finally {
      setPending(false);
    }
  };

  return (
    <div>
      <h1>Checkout</h1>
      <p style={{ color: '#52606d', margin: '0.5rem 0 1rem' }}>
        An order is created only if the checkout request succeeds.
      </p>
      {error && <div className="shop-alert error">{error}</div>}
      <form className="shop-form" onSubmit={onSubmit}>
        <textarea
          className="shop-textarea"
          rows={4}
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Shipping address"
          required
        />
        <button className="shop-btn" type="submit" disabled={pending}>
          {pending ? 'Placing order…' : 'Place order'}
        </button>
      </form>
    </div>
  );
}
