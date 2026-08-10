export interface Product {
  id: string;
  sku: string;
  name: string;
  brand: string;
  description: string;
  price_cents: number;
  specifications: Record<string, string>;
  version: number;
  category?: { id: string; name: string; slug: string } | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface Inventory {
  productId: string;
  quantity: number;
  reserved: number;
  available: number;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  limit: number;
}

export interface CartItem {
  productId: string;
  quantity: number;
  product: Product;
}

export interface Cart {
  items: CartItem[];
  totalCents: number;
  itemCount: number;
}

export interface Order {
  id: string;
  number: string;
  status: string;
  totalCents: number;
  items: { productId: string; quantity: number; unitPriceCents: number }[];
  createdAt: string;
}

export interface AuthResponse {
  accessToken: string;
  user: { id: string; email: string; name: string };
}

export interface AiChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AiChatRequest {
  messages: AiChatMessage[];
}

export interface AiChatResponse {
  answer: string;
  intent: string | null;
  sources: { product_id: string; content: string }[];
}
