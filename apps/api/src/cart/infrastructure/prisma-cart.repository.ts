import { Injectable } from '@nestjs/common';
import { Cart, CartItem } from '@prisma/client';
import { PrismaService } from '../../common/prisma/prisma.service';
import { CartItemWithProduct, CartRepository } from '../domain/cart.repository';

@Injectable()
export class PrismaCartRepository implements CartRepository {
  constructor(private readonly prisma: PrismaService) {}

  async getOrCreateForUser(userId: string): Promise<Cart> {
    const cart = await this.prisma.cart.findUnique({ where: { userId } });
    if (cart) return cart;
    return this.prisma.cart.create({ data: { userId } });
  }

  listItems(cartId: string): Promise<CartItemWithProduct[]> {
    return this.prisma.cartItem.findMany({
      where: { cartId },
      include: { product: { include: { category: true } } },
    });
  }

  async addItem(cartId: string, productId: string, quantity: number): Promise<CartItem> {
    return this.prisma.cartItem.upsert({
      where: { cartId_productId: { cartId, productId } },
      update: { quantity: { increment: quantity } },
      create: { cartId, productId, quantity },
    });
  }

  updateItemQuantity(
    cartId: string,
    productId: string,
    quantity: number,
  ): Promise<CartItem> {
    return this.prisma.cartItem.update({
      where: { cartId_productId: { cartId, productId } },
      data: { quantity },
    });
  }

  async removeItem(cartId: string, productId: string): Promise<void> {
    await this.prisma.cartItem.delete({
      where: { cartId_productId: { cartId, productId } },
    });
  }

  async clear(cartId: string): Promise<void> {
    await this.prisma.cartItem.deleteMany({ where: { cartId } });
  }
}
