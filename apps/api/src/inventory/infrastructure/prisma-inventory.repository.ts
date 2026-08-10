import { Injectable } from '@nestjs/common';
import { Inventory } from '@prisma/client';
import { PrismaService } from '../../common/prisma/prisma.service';
import { InventoryRepository } from '../domain/inventory.repository';

/**
 * Prisma-backed inventory repository.
 *
 * Mutations use atomic `updateMany ... update` guarded by conditions so
 * concurrent requests can never push quantity below zero.
 */
@Injectable()
export class PrismaInventoryRepository implements InventoryRepository {
  constructor(private readonly prisma: PrismaService) {}

  findByProductId(productId: string): Promise<Inventory | null> {
    return this.prisma.inventory.findUnique({ where: { productId } });
  }

  async adjustQuantity(productId: string, delta: number): Promise<Inventory> {
    const product = await this.prisma.product.findUnique({
      where: { id: productId },
      select: { id: true },
    });
    if (!product) {
      return this.upsert(productId, delta);
    }
    if (delta >= 0) {
      return this.prisma.inventory.update({
        where: { productId },
        data: { quantity: { increment: delta } },
      });
    }
    const updated = await this.prisma.inventory.updateMany({
      where: { productId, quantity: { gte: -delta } },
      data: { quantity: { decrement: -delta } },
    });
    if (updated.count === 0) {
      throw new Error('Insufficient stock');
    }
    return this.prisma.inventory.findUniqueOrThrow({ where: { productId } });
  }

  async adjustReserved(productId: string, delta: number): Promise<Inventory> {
    const updated = await this.prisma.inventory.updateMany({
      where: { productId, reserved: { gte: delta < 0 ? -delta : 0 } },
      data: { reserved: { increment: delta } },
    });
    if (updated.count === 0) {
      throw new Error('Cannot release more units than reserved');
    }
    return this.prisma.inventory.findUniqueOrThrow({ where: { productId } });
  }

  async setQuantity(productId: string, quantity: number): Promise<Inventory> {
    return this.prisma.inventory.update({
      where: { productId },
      data: { quantity },
    });
  }

  async upsert(productId: string, quantity: number): Promise<Inventory> {
    return this.prisma.inventory.upsert({
      where: { productId },
      update: { quantity },
      create: { productId, quantity },
    });
  }

  findLowStock(threshold: number): Promise<Inventory[]> {
    return this.prisma.inventory.findMany({
      where: { quantity: { lte: threshold } },
      include: { product: true },
      orderBy: { quantity: 'asc' },
    });
  }
}
