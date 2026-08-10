import { Inventory } from '@prisma/client';

export interface InventoryEntry {
  productId: string;
  quantity: number;
  reserved: number;
  available: number;
}

/**
 * Inventory persistence contract.
 *
 * Availability = quantity - reserved. All mutations are atomic at the
 * database level so concurrent orders cannot oversell.
 */
export interface InventoryRepository {
  findByProductId(productId: string): Promise<Inventory | null>;
  /** Atomically increment/decrement quantity, never below 0. */
  adjustQuantity(productId: string, delta: number): Promise<Inventory>;
  /** Atomically move quantity into reserved (or back). */
  adjustReserved(productId: string, delta: number): Promise<Inventory>;
  setQuantity(productId: string, quantity: number): Promise<Inventory>;
  upsert(productId: string, quantity: number): Promise<Inventory>;
  findLowStock(threshold: number): Promise<Inventory[]>;
}

export const INVENTORY_REPOSITORY = Symbol('INVENTORY_REPOSITORY');
