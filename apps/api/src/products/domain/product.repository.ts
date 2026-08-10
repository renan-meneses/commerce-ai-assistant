import { Product } from '@prisma/client';
import {
  CreateProductDto,
  ListProductsQuery,
  UpdateProductDto,
} from '../dto/product.dto';

/**
 * Domain contract for product persistence.
 *
 * The application layer depends on this interface, never on Prisma.
 * Swapping the implementation (Prisma, in-memory, another store)
 * requires no changes above the infrastructure boundary.
 */
export interface ProductRepository {
  findById(id: string): Promise<Product | null>;
  findBySku(sku: string): Promise<Product | null>;
  findMany(query: ListProductsQuery): Promise<{ items: Product[]; total: number }>;
  create(dto: CreateProductDto): Promise<Product>;
  update(id: string, dto: UpdateProductDto): Promise<Product>;
}

/** DI token used to bind the repository interface to its implementation. */
export const PRODUCT_REPOSITORY = Symbol('PRODUCT_REPOSITORY');
