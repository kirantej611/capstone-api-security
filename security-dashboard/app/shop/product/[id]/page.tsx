'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
  Product,
  Review,
  ShopApiError,
  addReview,
  addToCart,
  getProduct,
  getReviews,
  getShopUser,
} from '../../../../lib/shopApi';

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const productId = Number(params.id);
  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [qty, setQty] = useState(1);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [item, reviewList] = await Promise.all([getProduct(productId), getReviews(productId)]);
      setProduct(item);
      setReviews(reviewList);
    } catch (err) {
      setProduct(null);
      setError(err instanceof ShopApiError ? err.message : 'Could not load product');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (Number.isNaN(productId)) {
      setError('Invalid product id');
      setLoading(false);
      return;
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId]);

  const handleAdd = async () => {
    setNotice(null);
    setError(null);
    if (!getShopUser()) {
      setError('Sign in to add items to your cart.');
      return;
    }
    try {
      const result = await addToCart(productId, qty);
      setNotice(result.message);
    } catch (err) {
      setError(err instanceof ShopApiError ? err.message : 'Could not add to cart');
    }
  };

  const handleReview = async (event: FormEvent) => {
    event.preventDefault();
    setNotice(null);
    setError(null);
    if (!getShopUser()) {
      setError('Sign in to submit a review.');
      return;
    }
    if (!comment.trim()) {
      setError('Review comment is required.');
      return;
    }
    setSubmitting(true);
    try {
      const created = await addReview(productId, rating, comment.trim());
      setReviews((prev) => [created, ...prev]);
      setComment('');
      setNotice('Review saved.');
    } catch (err) {
      setError(err instanceof ShopApiError ? err.message : 'Could not save review');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="shop-loading">Loading product…</div>;
  if (error && !product) return <div className="shop-alert error">{error}</div>;
  if (!product) return <div className="shop-empty">Product not found.</div>;

  return (
    <div>
      <h1>{product.name}</h1>
      <p style={{ color: '#52606d', margin: '0.5rem 0 1rem' }}>{product.description}</p>
      <p className="shop-price">${product.price.toFixed(2)}</p>
      <p style={{ margin: '0.5rem 0 1rem' }}>
        Category: {product.category || 'uncategorized'} · Stock: {product.stock}
      </p>

      {error && <div className="shop-alert error">{error}</div>}
      {notice && <div className="shop-alert success">{notice}</div>}

      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '2rem' }}>
        <input
          className="shop-input"
          type="number"
          min={1}
          max={99}
          value={qty}
          onChange={(e) => setQty(Number(e.target.value))}
        />
        <button className="shop-btn" type="button" onClick={handleAdd}>
          Add to cart
        </button>
      </div>

      <h2>Reviews</h2>
      <form className="shop-form" onSubmit={handleReview} style={{ marginTop: '1rem' }}>
        <label>
          Rating
          <select className="shop-select" value={rating} onChange={(e) => setRating(Number(e.target.value))}>
            {[1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <textarea
          className="shop-textarea"
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Share how the product worked for you"
        />
        <button className="shop-btn" type="submit" disabled={submitting}>
          {submitting ? 'Saving…' : 'Submit review'}
        </button>
      </form>

      <div className="review-list">
        {reviews.length === 0 && <div className="shop-empty">No reviews yet.</div>}
        {reviews.map((review) => (
          <article key={review.id} className="review-item">
            <strong>
              {review.rating}/5 · user {review.user_id}
            </strong>
            <p>{review.comment}</p>
            <small>{review.created_at}</small>
          </article>
        ))}
      </div>
    </div>
  );
}
