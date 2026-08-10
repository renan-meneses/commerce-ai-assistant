import { Injectable } from '@nestjs/common';
import { Order, OrderStatus } from '@prisma/client';
import { OrderWithItems, OrderRepository } from '../domain/order.repository';
import { PrismaService } from '../../common/prisma/prisma.service';

@Injectable()
export class PrismaOrderRepository implements OrderRepository {
  constructor(private readonly prisma: PrismaService) {}

  findById(id: string): Promise<OrderWithItems | null> {
    return this.prisma.order.findUnique({
      where: { id },
      include: { items: true },
    });
  }

  findByNumber(number: string): Promise<OrderWithItems | null> {
    return this.prisma.order.findUnique({
      where: { number },
      include: { items: true },
    });
  }
  findManyForUser(userId: string): Promise<OrderWithItems[]> {
    return this.prisma.order.findMany({
      where: { userId },
      include: { items: true },
      orderBy: { createdAt: 'desc' },
    });
  }

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
  }): Promise<OrderWithItems> {
    return this.prisma.order.create({
      data: {
        number: data.number,
        userId: data.userId,
        totalCents: data.totalCents,
        shippingCents: data.shippingCents,
        items: { create: data.items },
      },
      include: { items: true },
    });
  }

  updateStatus(id: string, status: OrderStatus): Promise<Order> {
    return this.prisma.order.update({ where: { id }, data: { status } });
  }
}
