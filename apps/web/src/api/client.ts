import type {
  AiChatRequest,
  AiChatResponse,
  AuthResponse,
  Cart,
  Inventory,
  Order,
  Product,
  ProductListResponse,
} from './types';

const TOKEN_KEY = 'commerce.token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      const detail = Array.isArray(body.message) ? body.message.join(', ') : body.message;
      if (detail) message = detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (name: string, email: string, password: string) =>
    request<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),

  listProducts: (params: { page?: number; limit?: number; search?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.limit) query.set('limit', String(params.limit));
    if (params.search) query.set('search', params.search);
    const suffix = query.toString() ? `?${query.toString()}` : '';
    return request<ProductListResponse>(`/api/v1/products${suffix}`);
  },

  getProduct: (id: string) => request<Product>(`/api/v1/products/${id}`),

  getInventory: (id: string) =>
    request<Inventory>(`/api/v1/products/${id}/inventory`),

  getCart: () => request<Cart>('/api/v1/cart'),

  addCartItem: (productId: string, quantity: number) =>
    request<Cart>('/api/v1/cart/items', {
      method: 'POST',
      body: JSON.stringify({ productId, quantity }),
    }),

  updateCartItem: (productId: string, quantity: number) =>
    request<Cart>(`/api/v1/cart/items/${productId}`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity }),
    }),

  removeCartItem: (productId: string) =>
    request<Cart>(`/api/v1/cart/items/${productId}`, { method: 'DELETE' }),

  clearCart: () => request<Cart>('/api/v1/cart', { method: 'DELETE' }),

  getOrders: () => request<Order[]>('/api/v1/orders'),

  checkout: () => request<Order>('/api/v1/orders', { method: 'POST' }),

  aiChat: (payload: AiChatRequest) =>
    request<AiChatResponse>('/ai/api/v1/ai/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
