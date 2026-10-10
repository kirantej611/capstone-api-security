import { getGatewayUrl } from './serviceUrls';

const TOKEN_KEY = 'aurora.shop.token';
const USER_KEY = 'aurora.shop.user';

export interface ShopUser {
  user_id: number;
  username: string;
  role: string;
}

export interface Product {
  id: number;
  name: string;
  description: string | null;
  price: number;
  image_url: string | null;
  category: string | null;
  stock: number;
}

export interface Review {
  id: number;
  product_id: number;
  user_id: number;
  rating: number;
  comment: string;
  created_at: string;
}

export interface CartItem {
  item_id: number;
  name: string;
  qty: number;
  unit_price: number;
  line_total: number;
}

export interface CartResponse {
  user_id: number;
  items: CartItem[];
  total: number;
}

export interface OrderItem {
  product_id: number;
  quantity: number;
  price: number;
  name?: string | null;
}

export interface Order {
  id: number;
  user_id: number;
  total: number;
  status: string;
  shipping_address: string | null;
  items: OrderItem[];
  created_at: string;
}

export class ShopApiError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = 'ShopApiError';
    this.status = status;
    this.body = body;
  }
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getShopUser(): ShopUser | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as ShopUser;
  } catch {
    return null;
  }
}

export function setSession(token: string, user: ShopUser) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

function detailMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (item && typeof item === 'object' && 'msg' in item) {
            return String((item as { msg: string }).msg);
          }
          return JSON.stringify(item);
        })
        .join('; ');
    }
  }
  return fallback;
}

export async function shopRequest<T>(
  path: string,
  init: RequestInit = {},
  opts: { auth?: boolean } = {}
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('Accept', 'application/json');
  if (opts.auth !== false) {
    const token = getToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${getGatewayUrl()}${path}`, {
      ...init,
      headers,
      cache: 'no-store',
    });
  } catch {
    throw new ShopApiError(
      'Cannot reach the store API through the gateway. Confirm the API gateway is running on port 8080.',
      0,
      null
    );
  }

  const contentType = response.headers.get('content-type') || '';
  let body: unknown = null;
  if (contentType.includes('application/json')) {
    body = await response.json();
  } else {
    const text = await response.text();
    body = text || null;
  }

  if (!response.ok) {
    throw new ShopApiError(
      detailMessage(body, `Request failed with HTTP ${response.status}`),
      response.status,
      body
    );
  }

  return body as T;
}

export function listProducts(params?: { category?: string; q?: string }) {
  if (params?.q?.trim()) {
    return shopRequest<{ query: string; results: Product[]; count: number }>(
      `/api/search?q=${encodeURIComponent(params.q.trim())}`,
      {},
      { auth: false }
    );
  }
  const query = new URLSearchParams();
  if (params?.category) query.set('category', params.category);
  query.set('limit', '100');
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return shopRequest<Product[]>(`/api/products${suffix}`, {}, { auth: false });
}

export function listCategories() {
  return shopRequest<string[]>('/api/categories', {}, { auth: false });
}

export function getProduct(id: number) {
  return shopRequest<Product>(`/api/products/${id}`, {}, { auth: false });
}

export function getReviews(productId: number) {
  return shopRequest<Review[]>(`/api/products/${productId}/reviews`, {}, { auth: false });
}

export function addReview(productId: number, rating: number, comment: string) {
  return shopRequest<Review>(`/api/products/${productId}/reviews`, {
    method: 'POST',
    body: JSON.stringify({ rating, comment }),
  });
}

export function registerUser(username: string, email: string, password: string) {
  return shopRequest<{ message: string; success: boolean }>(
    '/api/auth/register',
    {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    },
    { auth: false }
  );
}

export function loginUser(username: string, password: string) {
  return shopRequest<{
    token: string;
    user_id: number;
    username: string;
    role: string;
    message: string;
  }>(
    '/api/login',
    {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    },
    { auth: false }
  );
}

export function getCart() {
  return shopRequest<CartResponse>('/api/cart');
}

export function addToCart(itemId: number, qty: number) {
  return shopRequest<{ message: string; success: boolean }>('/api/cart/add', {
    method: 'POST',
    body: JSON.stringify({ item_id: itemId, qty }),
  });
}

export function removeCartItem(productId: number) {
  return shopRequest<{ message: string }>(`/api/cart/items/${productId}`, {
    method: 'DELETE',
  });
}

export function checkout(shippingAddress: string) {
  return shopRequest<Order>('/api/checkout', {
    method: 'POST',
    body: JSON.stringify({ shipping_address: shippingAddress }),
  });
}

export function listOrders() {
  return shopRequest<Order[]>('/api/orders');
}

export function getOrder(id: number) {
  return shopRequest<Order>(`/api/orders/${id}`);
}

export function getProfile() {
  return shopRequest<{
    id: number;
    username: string;
    email: string | null;
    role: string;
    created_at: string;
  }>('/api/user/profile');
}
