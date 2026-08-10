import { BadRequestException, Inject, Injectable } from '@nestjs/common';
import { Cart } from '@prisma/client';
import { InventoryService } from '../inventory/inventory.service';
import {
  CartItemWithProduct,
  CartRepository,
  CART_REPOSITORY,
} from './domain/cart.repository';
import { AddCartItemDto } from './dto/cart.dto';

export interface CartView {
  id: string;
  items: Array<{
    id: string;
    productId: string;
    name: string;
    brand: string;
    unitPriceCents: number;
    quantity: number;
    lineTotalCents: number;
  }>;
  subtotalCents: number;
  itemCount: number;
}

/**
 * Cart application service.
 *
 * Prices are always read from the current product record at view time —
 * never stored on the cart item — so totals can never go stale.
 */
@Injectable()
export class CartService {
  constructor(
    @Inject(CART_REPOSITORY) private readonly repository: CartRepository,
    private readonly inventoryService: InventoryService,
  ) {}

  async view(userId: string): Promise<CartView> {
    const cart = await this.repository.getOrCreateForUser(userId);
    return this.toView(cart, await this.repository.listItems(cart.id));
  }

  async addItem(userId: string, dto: AddCartItemDto): Promise<CartView> {
    const available = await this.inventoryService.isAvailable(
      dto.productId,
      dto.quantity,
    );
    if (!available) {
      throw new BadRequestException(
        `Product ${dto.productId} does not have ${dto.quantity} units available`,
      );
    }
    const cart = await this.repository.getOrCreateForUser(userId);
    await this.repository.addItem(cart.id, dto.productId, dto.quantity);
    return this.toView(cart, await this.repository.listItems(cart.id));
  }

  async updateItem(
    userId: string,
    productId: string,
    quantity: number,
  ): Promise<CartView> {
    const cart = await this.repository.getOrCreateForUser(userId);
    const available = await this.inventoryService.isAvailable(productId, quantity);
    if (!available) {
      throw new BadRequestException(
        `Product ${productId} does not have ${quantity} units available`,
      );
    }
    await this.repository.updateItemQuantity(cart.id, productId, quantity);
    return this.toView(cart, await this.repository.listItems(cart.id));
  }

  async removeItem(userId: string, productId: string): Promise<CartView> {
    const cart = await this.repository.getOrCreateForUser(userId);
    await this.repository.removeItem(cart.id, productId);
    return this.toView(cart, await this.repository.listItems(cart.id));
  }

  async clear(userId: string): Promise<void> {
    const cart = await this.repository.getOrCreateForUser(userId);
    await this.repository.clear(cart.id);
  }

  private toView(cart: Cart, items: CartItemWithProduct[]): CartView {
    const viewItems = items.map((item) => ({
      id: item.id,
      productId: item.productId,
      name: item.product.name,
      brand: item.product.brand,
      unitPriceCents: item.product.priceCents,
      quantity: item.quantity,
      lineTotalCents: item.quantity * item.product.priceCents,
    }));

    return {
      id: cart.id,
      items: viewItems,
      subtotalCents: viewItems.reduce((sum, i) => sum + i.lineTotalCents, 0),
      itemCount: viewItems.reduce((sum, i) => sum + i.quantity, 0),
    };
  }
}
