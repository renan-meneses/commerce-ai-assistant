import {
  BadRequestException,
  ForbiddenException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { Order, OrderStatus } from '@prisma/client';
import { randomUUID } from 'crypto';
import { PrismaService } from '../common/prisma/prisma.service';
import { InventoryService } from '../inventory/inventory.service';
import {
  CartRepository,
  CartItemWithProduct,
  CART_REPOSITORY,
} from '../cart/domain/cart.repository';
import {
  OrderRepository,
  OrderWithItems,
  ORDER_REPOSITORY,
} from './domain/order.repository';

export interface CreateOrderResult {
  order: Order;
  reserved: boolean;
}

/**
 * Order application service.
 *
 * Order creation is transactional:
 *   1. load cart items with live prices;
 *   2. validate availability for every line;
 *   3. decrement stock (commit reservation) inside the DB transaction;
 *   4. create order + order items;
 *   5. clear the cart.
 *
 * The stock decrement and order creation share one Prisma transaction,
 * so a failure on any step rolls everything back.
 */
@Injectable()
export class OrdersService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly inventoryService: InventoryService,
    @Inject(ORDER_REPOSITORY) private readonly orderRepository: OrderRepository,
    @Inject(CART_REPOSITORY) private readonly cartRepository: CartRepository,
  ) {}

  async createFromCart(userId: string): Promise<CreateOrderResult> {
    const cart = await this.cartRepository.getOrCreateForUser(userId);
    const items = await this.cartRepository.listItems(cart.id);
    if (items.length === 0) {
      throw new BadRequestException('Cart is empty');
    }

    await this.validateAvailability(items);

    const shippingCents = this.calculateShipping(items);
    const subtotal = items.reduce((sum, i) => sum + i.quantity * i.product.priceCents, 0);
    const number = this.generateOrderNumber();

    const order = await this.prisma.$transaction(async (tx) => {
      for (const item of items) {
        const result = await tx.inventory.updateMany({
          where: { productId: item.productId, quantity: { gte: item.quantity } },
          data: { quantity: { decrement: item.quantity } },
        });
        if (result.count === 0) {
          throw new BadRequestException(`Insufficient stock for ${item.product.name}`);
        }
      }
      const created = await tx.order.create({
        data: {
          number,
          userId,
          totalCents: subtotal + shippingCents,
          shippingCents,
          items: {
            create: items.map((item) => ({
              productId: item.productId,
              productName: item.product.name,
              unitPriceCents: item.product.priceCents,
              quantity: item.quantity,
            })),
          },
        },
        include: { items: true },
      });
      await tx.cartItem.deleteMany({ where: { cartId: cart.id } });
      return created;
    });

    return { order, reserved: true };
  }

  async getById(userId: string, orderId: string): Promise<OrderWithItems> {
    const order = await this.orderRepository.findById(orderId);
    if (!order) {
      throw new NotFoundException(`Order ${orderId} not found`);
    }
    if (order.userId !== userId) {
      throw new ForbiddenException('Order does not belong to this user');
    }
    return order;
  }

  async getByNumber(userId: string, number: string): Promise<OrderWithItems> {
    const order = await this.orderRepository.findByNumber(number);
    if (!order) {
      throw new NotFoundException(`Order ${number} not found`);
    }
    if (order.userId !== userId) {
      throw new ForbiddenException('Order does not belong to this user');
    }
    return order;
  }

  async listForUser(userId: string): Promise<OrderWithItems[]> {
    return this.orderRepository.findManyForUser(userId);
  }

  /** For the AI assistant tool: return status + tracking summary. */
  async getStatusForAssistant(userId: string, number: string): Promise<unknown> {
    const order = await this.getByNumber(userId, number);
    return {
      number: order.number,
      status: order.status,
      totalCents: order.totalCents,
      items: order.items.map((i) => ({
        productName: i.productName,
        quantity: i.quantity,
      })),
      createdAt: order.createdAt,
    };
  }

  async updateStatus(orderId: string, status: OrderStatus): Promise<Order> {
    return this.orderRepository.updateStatus(orderId, status);
  }

  private async validateAvailability(items: CartItemWithProduct[]): Promise<void> {
    for (const item of items) {
      const available = await this.inventoryService.isAvailable(
        item.productId,
        item.quantity,
      );
      if (!available) {
        throw new BadRequestException(`Insufficient stock for ${item.product.name}`);
      }
    }
  }

  private calculateShipping(items: CartItemWithProduct[]): number {
    const units = items.reduce((sum, i) => sum + i.quantity, 0);
    const subtotal = items.reduce((sum, i) => sum + i.quantity * i.product.priceCents, 0);
    if (subtotal >= 300_00) return 0;
    return Math.max(1500, units * 500); // R$15 base, R$5 per unit
  }

  private generateOrderNumber(): string {
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    return `ORD-${date}-${randomUUID().slice(0, 6).toUpperCase()}`;
  }
}
