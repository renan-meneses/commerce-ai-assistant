import { Inject, Injectable, NotFoundException } from '@nestjs/common';
import { Product } from '@prisma/client';
import { ProductRepository, PRODUCT_REPOSITORY } from './domain/product.repository';
import { CreateProductDto, ListProductsQuery, UpdateProductDto } from './dto/product.dto';

export interface ProductDomainEvent {
  type: 'product.created' | 'product.updated';
  productId: string;
  version: number;
  occurredAt: string;
}

/**
 * Product application service (use case layer).
 *
 * Depends on the ProductRepository interface — no Prisma types or
 * database primitives leak into this layer.
 */
@Injectable()
export class ProductsService {
  constructor(
    @Inject(PRODUCT_REPOSITORY) private readonly repository: ProductRepository,
  ) {}

  async findAll(query: ListProductsQuery): Promise<{
    items: Product[];
    total: number;
    page: number;
    limit: number;
    pages: number;
  }> {
    const { items, total } = await this.repository.findMany(query);
    const page = query.page ?? 1;
    const limit = query.limit ?? 20;
    return { items, total, page, limit, pages: Math.ceil(total / limit) };
  }

  async findOne(id: string): Promise<Product> {
    const product = await this.repository.findById(id);
    if (!product) {
      throw new NotFoundException(`Product ${id} not found`);
    }
    return product;
  }

  async create(dto: CreateProductDto): Promise<Product> {
    return this.repository.create(dto);
  }

  async update(id: string, dto: UpdateProductDto): Promise<Product> {
    await this.findOne(id);
    return this.repository.update(id, dto);
  }

  /** Emitted after successful create/update so async indexing can react. */
  async buildEvent(product: Product): Promise<ProductDomainEvent> {
    return {
      type: 'product.updated',
      productId: product.id,
      version: product.version,
      occurredAt: new Date().toISOString(),
    };
  }
}
