'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  Product,
  ShopApiError,
  addToCart,
  getShopUser,
  listCategories,
  listProducts,
} from '../../lib/shopApi';

const TILES: Record<string, { bg: string; emoji: string }> = {
  electronics: { bg: '#dbeafe', emoji: '💻' },
  clothing: { bg: '#fce7f3', emoji: '👕' },
  books: { bg: '#fef3c7', emoji: '📘' },
  home: { bg: '#dcfce7', emoji: '🏠' },
};

export default function ShopCatalogPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState('all');
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [categoryList, productResult] = await Promise.all([
          listCategories(),
          listProducts(
            submittedQuery
              ? { q: submittedQuery }
              : category !== 'all'
                ? { category }
                : undefined
          ),
        ]);
        if (cancelled) return;
        setCategories(categoryList);
        setProducts(Array.isArray(productResult) ? productResult : productResult.results);
      } catch (err) {
        if (!cancelled) {
          setProducts([]);
          setError(err instanceof ShopApiError ? err.message : 'Failed to load products');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [category, submittedQuery]);

  const title = useMemo(() => {
    if (submittedQuery) return `Search results for “${submittedQuery}”`;
    if (category !== 'all') return category;
    return 'New arrivals';
  }, [category, submittedQuery]);

  const onSearch = (event: FormEvent) => {
    event.preventDefault();
    setSubmittedQuery(query.trim());
    setCategory('all');
  };

  const handleAdd = async (product: Product) => {
    setNotice(null);
    setError(null);
    if (!getShopUser()) {
      setError('Sign in to add items to your cart.');
      return;
    }
    try {
      const result = await addToCart(product.id, 1);
      setNotice(result.message);
    } catch (err) {
      setError(err instanceof ShopApiError ? err.message : 'Could not add to cart');
    }
  };

  return (
    <div>
      <section className="shop-hero">
        <h1>Aurora Boutique</h1>
        <p>Everyday catalog served from the live e-commerce API through the gateway.</p>
      </section>

      <form className="shop-toolbar" onSubmit={onSearch}>
        <input
          className="shop-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search products"
          aria-label="Search products"
        />
        <select
          className="shop-select"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setSubmittedQuery('');
          }}
          aria-label="Category"
        >
          <option value="all">All categories</option>
          {categories.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <button className="shop-btn" type="submit">
          Search
        </button>
      </form>

      {error && <div className="shop-alert error">{error}</div>}
      {notice && <div className="shop-alert success">{notice}</div>}
      {loading && <div className="shop-loading">Loading products…</div>}
      {!loading && !error && products.length === 0 && (
        <div className="shop-empty">No products matched this search.</div>
      )}

      <h2 style={{ marginBottom: '1rem', textTransform: 'capitalize' }}>{title}</h2>
      <div className="shop-grid">
        {products.map((product) => {
          const tile = TILES[product.category || ''] || { bg: '#e5e7eb', emoji: '🛍️' };
          return (
            <article key={product.id} className="shop-card">
              <div className="shop-card-media" style={{ background: tile.bg }}>
                {tile.emoji}
              </div>
              <div className="shop-card-body">
                <strong>{product.name}</strong>
                <p style={{ color: '#52606d', fontSize: '0.88rem' }}>{product.description}</p>
                <span className="shop-price">${product.price.toFixed(2)}</span>
                <span style={{ fontSize: '0.8rem', color: '#7b8794' }}>In stock: {product.stock}</span>
                <Link href={`/shop/product/${product.id}`}>View details</Link>
                <button className="shop-btn" type="button" onClick={() => handleAdd(product)}>
                  Add to cart
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
