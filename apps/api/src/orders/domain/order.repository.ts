import { Order, OrderItem, OrderStatus, Prisma } from '@prisma/client';

export type OrderWithItems = Prisma.OrderGetPayload<{
  include: { items: true };
}>;

export interface OrderRepository {
  findById(id: string): Promise<OrderWithItems | null>;
  findByNumber(number: string): Promise<OrderWithItems | null>;
  findManyForUser(userId: string): Promise<OrderWithItems[]>;
  create(data: {
    number: string;
    userId: string;
    totalCents: number;
    shippingCents: number;
    items: Array<{
      productId: string;
      productName: string;
      unitPriceCents: number;
      quantity: number;
    }>;
  }): Promise<OrderWithItems>;
  updateStatus(id: string, status: OrderStatus): Promise<Order>;
}

export const ORDER_REPOSITORY = Symbol('ORDER_REPOSITORY');
