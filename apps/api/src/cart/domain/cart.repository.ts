import { Cart, CartItem, Prisma } from '@prisma/client';

export type CartItemWithProduct = CartItem & {
  product: Prisma.ProductGetPayload<{ include: { category: true } }>;
};

export interface CartRepository {
  getOrCreateForUser(userId: string): Promise<Cart>;
  listItems(cartId: string): Promise<CartItemWithProduct[]>;
  addItem(cartId: string, productId: string, quantity: number): Promise<CartItem>;
  updateItemQuantity(
    cartId: string,
    productId: string,
    quantity: number,
  ): Promise<CartItem>;
  removeItem(cartId: string, productId: string): Promise<void>;
  clear(cartId: string): Promise<void>;
}

export const CART_REPOSITORY = Symbol('CART_REPOSITORY');
