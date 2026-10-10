'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShopApiError, loginUser, setSession } from '../../../lib/shopApi';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
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
      const response = await loginUser(username, password);
      setSession(response.token, {
        user_id: response.user_id,
        username: response.username,
        role: response.role,
      });
      setResult(`${response.message} Signed in as ${response.username} (role: ${response.role}).`);
      router.push('/shop');
    } catch (err) {
      setError(err instanceof ShopApiError ? err.message : 'Login failed');
    } finally {
      setPending(false);
    }
  };

  return (
    <div>
      <h1>Sign in</h1>
      <p style={{ color: '#52606d', margin: '0.5rem 0 1rem' }}>
        Authentication is submitted to the live login API through the gateway.
      </p>
      {error && <div className="shop-alert error">{error}</div>}
      {result && <div className="shop-alert success">{result}</div>}
      <form className="shop-form" onSubmit={onSubmit}>
        <input
          className="shop-input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
        />
        <input
          className="shop-input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />
        <button className="shop-btn" type="submit" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}
