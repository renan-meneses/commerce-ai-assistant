import {
  BadRequestException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { InventoryRepository, INVENTORY_REPOSITORY } from './domain/inventory.repository';
import { InventoryEntry } from './domain/inventory.repository';

/**
 * Inventory application service.
 *
 * Business rules:
 * - available = quantity - reserved
 * - stock can never go negative
 * - reservations are guarded by atomic DB conditions
 */
@Injectable()
export class InventoryService {
  constructor(
    @Inject(INVENTORY_REPOSITORY) private readonly repository: InventoryRepository,
  ) {}

  async getByProduct(productId: string): Promise<InventoryEntry> {
    const inventory = await this.repository.findByProductId(productId);
    if (!inventory) {
      throw new NotFoundException(`No inventory for product ${productId}`);
    }
    return this.toEntry(inventory);
  }

  async isAvailable(productId: string, quantity = 1): Promise<boolean> {
    const inventory = await this.repository.findByProductId(productId);
    if (!inventory) return false;
    return inventory.quantity - inventory.reserved >= quantity;
  }

  async restock(productId: string, delta: number): Promise<InventoryEntry> {
    const inventory = await this.repository.adjustQuantity(productId, delta);
    return this.toEntry(inventory);
  }

  async reserve(productId: string, quantity: number): Promise<InventoryEntry> {
    const inventory = await this.repository.findByProductId(productId);
    if (!inventory) {
      throw new BadRequestException(`Product ${productId} has no stock record`);
    }
    if (inventory.quantity - inventory.reserved < quantity) {
      throw new BadRequestException(
        `Insufficient stock for product ${productId} (available: ${inventory.quantity - inventory.reserved})`,
      );
    }
    const updated = await this.repository.adjustReserved(productId, quantity);
    return this.toEntry(updated);
  }

  async release(productId: string, quantity: number): Promise<InventoryEntry> {
    const inventory = await this.repository.adjustReserved(productId, -quantity);
    return this.toEntry(inventory);
  }

  async commitReservation(productId: string, quantity: number): Promise<InventoryEntry> {
    const inventory = await this.repository.adjustQuantity(productId, -quantity);
    await this.repository.adjustReserved(productId, -quantity);
    return this.toEntry(inventory);
  }

  async lowStock(threshold = 5): Promise<unknown[]> {
    return this.repository.findLowStock(threshold);
  }

  private toEntry(inventory: {
    productId: string;
    quantity: number;
    reserved: number;
  }): InventoryEntry {
    return {
      productId: inventory.productId,
      quantity: inventory.quantity,
      reserved: inventory.reserved,
      available: inventory.quantity - inventory.reserved,
    };
  }
}
