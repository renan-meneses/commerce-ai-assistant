import { NotFoundException } from '@nestjs/common';
import { Product } from '@prisma/client';
import { ProductsService } from './products.service';
import { ProductRepository, PRODUCT_REPOSITORY } from './domain/product.repository';

describe('ProductsService', () => {
  const mockProduct = {
    id: 'p-1',
    sku: 'NB-TEST',
    name: 'Test Notebook',
    brand: 'ASUS',
    priceCents: 499900,
    version: 1,
  } as unknown as Product;

  let service: ProductsService;
  let repository: jest.Mocked<ProductRepository>;

  beforeEach(() => {
    repository = {
      findById: jest.fn(),
      findBySku: jest.fn(),
      findMany: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
    };
    service = new ProductsService(repository);
  });

  it('returns a paginated result', async () => {
    repository.findMany.mockResolvedValue({ items: [mockProduct], total: 1 });

    const result = await service.findAll({ page: 1, limit: 20 });

    expect(result.total).toBe(1);
    expect(result.pages).toBe(1);
    expect(result.items[0].id).toBe('p-1');
  });

  it('throws NotFoundException when product does not exist', async () => {
    repository.findById.mockResolvedValue(null);

    await expect(service.findOne('missing')).rejects.toThrow(NotFoundException);
  });

  it('creates a product through the repository', async () => {
    repository.create.mockResolvedValue(mockProduct);

    const result = await service.create({
      sku: 'NB-TEST',
      name: 'Test Notebook',
      description: 'A notebook for testing purposes in the catalog.',
      categoryId: 'cat-1',
      brand: 'ASUS',
      priceCents: 499900,
    });

    expect(repository.create).toHaveBeenCalledTimes(1);
    expect(result.sku).toBe('NB-TEST');
  });

  it('builds a domain event with current product version', async () => {
    const event = await service.buildEvent(mockProduct);

    expect(event.type).toBe('product.updated');
    expect(event.productId).toBe('p-1');
    expect(event.version).toBe(1);
  });

  it('exposes the DI token used by the module', () => {
    expect(PRODUCT_REPOSITORY.toString()).toContain('PRODUCT_REPOSITORY');
  });
});
