import { Prisma, Product } from '@prisma/client';
import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../../common/prisma/prisma.service';
import { ProductRepository } from '../domain/product.repository';
import {
  CreateProductDto,
  ListProductsQuery,
  UpdateProductDto,
} from '../dto/product.dto';

/**
 * Prisma-backed ProductRepository. The only place where product
 * persistence touches Prisma directly.
 *
 * Query building for listing (filters, pagination, sorting) lives here
 * as infrastructure concern; the service stays store-agnostic.
 */
@Injectable()
export class PrismaProductRepository implements ProductRepository {
  private readonly logger = new Logger(PrismaProductRepository.name);

  constructor(private readonly prisma: PrismaService) {}

  findById(id: string): Promise<Product | null> {
    return this.prisma.product.findUnique({
      where: { id },
      include: { category: true, inventory: true },
    });
  }

  findBySku(sku: string): Promise<Product | null> {
    return this.prisma.product.findUnique({ where: { sku } });
  }

  async findMany(query: ListProductsQuery): Promise<{ items: Product[]; total: number }> {
    const where = this.buildWhere(query);
    const orderBy = this.buildOrderBy(query);

    const [items, total] = await this.prisma.$transaction([
      this.prisma.product.findMany({
        where,
        orderBy,
        skip: (query.page! - 1) * query.limit!,
        take: query.limit!,
        include: { category: true, inventory: true },
      }),
      this.prisma.product.count({ where }),
    ]);

    return { items, total };
  }

  create(dto: CreateProductDto): Promise<Product> {
    return this.prisma.product.create({
      data: {
        sku: dto.sku,
        name: dto.name,
        description: dto.description,
        categoryId: dto.categoryId,
        brand: dto.brand,
        priceCents: dto.priceCents,
        specifications: (dto.specifications as Prisma.InputJsonValue) ?? undefined,
      },
      include: { category: true },
    });
  }

  async update(id: string, dto: UpdateProductDto): Promise<Product> {
    return this.prisma.product.update({
      where: { id },
      data: {
        ...(dto.name !== undefined && { name: dto.name }),
        ...(dto.description !== undefined && { description: dto.description }),
        ...(dto.priceCents !== undefined && { priceCents: dto.priceCents }),
        ...(dto.active !== undefined && { active: dto.active }),
        ...(dto.specifications !== undefined && {
          specifications: dto.specifications as Prisma.InputJsonValue,
        }),
        version: { increment: 1 },
      },
      include: { category: true },
    });
  }

  private buildWhere(query: ListProductsQuery): Prisma.ProductWhereInput {
    const where: Prisma.ProductWhereInput = { active: true };

    if (query.q) {
      where.OR = [
        { name: { contains: query.q, mode: 'insensitive' } },
        { description: { contains: query.q, mode: 'insensitive' } },
        { brand: { contains: query.q, mode: 'insensitive' } },
      ];
    }
    if (query.category) {
      where.category = { slug: query.category };
    }
    if (query.brand) {
      where.brand = query.brand;
    }
    if (query.minPriceCents !== undefined) {
      where.priceCents = { ...(where.priceCents as object), gte: query.minPriceCents };
    }
    if (query.maxPriceCents !== undefined) {
      where.priceCents = {
        ...(where.priceCents as object),
        lte: query.maxPriceCents,
      };
    }
    return where;
  }

  private buildOrderBy(query: ListProductsQuery): Prisma.ProductOrderByWithRelationInput {
    const field = query.sortBy ?? 'name';
    const direction: Prisma.SortOrder = query.order === 'desc' ? 'desc' : 'asc';
    if (['name', 'priceCents', 'brand', 'createdAt'].includes(field)) {
      return { [field]: direction };
    }
    return { name: direction };
  }
}
