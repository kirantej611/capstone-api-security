'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { ShopApiError, registerUser } from '../../../lib/shopApi';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setResult(null);
    setPending(true);
    try {
      const response = await registerUser(username, email, password);
      setResult(response.message);
    } catch (err) {
      setError(err instanceof ShopApiError ? err.message : 'Registration failed');
    } finally {
      setPending(false);
    }
  };

  return (
    <div>
      <h1>Create account</h1>
      {error && <div className="shop-alert error">{error}</div>}
      {result && (
        <div className="shop-alert success">
          {result} You can now <Link href="/shop/login">sign in</Link>.
        </div>
      )}
      <form className="shop-form" onSubmit={onSubmit}>
        <input className="shop-input" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" required />
        <input className="shop-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
        <input className="shop-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
        <button className="shop-btn" type="submit" disabled={pending}>
          {pending ? 'Creating…' : 'Create account'}
        </button>
      </form>
    </div>
  );
}
