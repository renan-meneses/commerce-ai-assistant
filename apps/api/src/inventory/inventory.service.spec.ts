import { BadRequestException, NotFoundException } from '@nestjs/common';
import { InventoryService } from './inventory.service';
import { InventoryRepository } from './domain/inventory.repository';

describe('InventoryService', () => {
  let service: InventoryService;
  let repository: jest.Mocked<InventoryRepository>;

  beforeEach(() => {
    repository = {
      findByProductId: jest.fn(),
      adjustQuantity: jest.fn(),
      adjustReserved: jest.fn(),
      setQuantity: jest.fn(),
      upsert: jest.fn(),
      findLowStock: jest.fn(),
    };
    service = new InventoryService(repository);
  });

  it('computes available = quantity - reserved', async () => {
    repository.findByProductId.mockResolvedValue({
      id: 'inv-1',
      productId: 'p-1',
      quantity: 10,
      reserved: 3,
      updatedAt: new Date(),
    });

    const entry = await service.getByProduct('p-1');
    expect(entry.available).toBe(7);
  });

  it('rejects reservation when stock is insufficient', async () => {
    repository.findByProductId.mockResolvedValue({
      id: 'inv-1',
      productId: 'p-1',
      quantity: 2,
      reserved: 0,
      updatedAt: new Date(),
    });

    await expect(service.reserve('p-1', 5)).rejects.toThrow(BadRequestException);
  });

  it('throws NotFoundException when product has no inventory', async () => {
    repository.findByProductId.mockResolvedValue(null);

    await expect(service.getByProduct('p-x')).rejects.toThrow(NotFoundException);
  });

  it('reports availability correctly', async () => {
    repository.findByProductId.mockResolvedValue({
      id: 'inv-1',
      productId: 'p-1',
      quantity: 5,
      reserved: 5,
      updatedAt: new Date(),
    });

    await expect(service.isAvailable('p-1', 1)).resolves.toBe(false);
  });
});
