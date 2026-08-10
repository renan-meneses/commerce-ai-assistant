import { BadRequestException } from '@nestjs/common';
import { OrdersService } from './orders.service';
import { InventoryService } from '../inventory/inventory.service';
import { CartRepository, CartItemWithProduct } from '../cart/domain/cart.repository';
import { OrderRepository } from './domain/order.repository';
import { PrismaService } from '../common/prisma/prisma.service';

describe('OrdersService', () => {
  let service: OrdersService;
  const txMock = {
    inventory: { updateMany: jest.fn() },
    order: { create: jest.fn() },
    cartItem: { deleteMany: jest.fn() },
  };
  const prisma = {
    $transaction: jest.fn((fn: (tx: typeof txMock) => Promise<unknown>) => fn(txMock)),
    inventory: { updateMany: jest.fn() },
    order: { create: jest.fn() },
    cartItem: { deleteMany: jest.fn() },
  };
  const inventory = {
    isAvailable: jest.fn(),
    reserve: jest.fn(),
    release: jest.fn(),
    commitReservation: jest.fn(),
    getByProduct: jest.fn(),
    restock: jest.fn(),
    lowStock: jest.fn(),
  };
  const cartRepository: jest.Mocked<CartRepository> = {
    getOrCreateForUser: jest.fn(),
    listItems: jest.fn(),
    addItem: jest.fn(),
    updateItemQuantity: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  };
  const orderRepository: jest.Mocked<OrderRepository> = {
    findById: jest.fn(),
    findByNumber: jest.fn(),
    findManyForUser: jest.fn(),
    create: jest.fn(),
    updateStatus: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    service = new OrdersService(
      prisma as unknown as PrismaService,
      inventory as unknown as InventoryService,
      orderRepository,
      cartRepository,
    );
  });

  it('rejects order creation with an empty cart', async () => {
    cartRepository.getOrCreateForUser.mockResolvedValue({ id: 'cart-1' } as never);
    cartRepository.listItems.mockResolvedValue([]);

    await expect(service.createFromCart('user-1')).rejects.toThrow(BadRequestException);
  });

  it('creates an order transactionally when stock is sufficient', async () => {
    const item = {
      id: 'ci-1',
      cartId: 'cart-1',
      productId: 'p-1',
      quantity: 2,
      createdAt: new Date(),
      product: {
        id: 'p-1',
        sku: 'SKU',
        name: 'Notebook',
        brand: 'ASUS',
        description: 'd',
        categoryId: 'c',
        priceCents: 500000,
        currency: 'BRL',
        specifications: null,
        version: 1,
        active: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      } as CartItemWithProduct['product'],
    } as CartItemWithProduct;

    cartRepository.getOrCreateForUser.mockResolvedValue({ id: 'cart-1' } as never);
    cartRepository.listItems.mockResolvedValue([item]);
    inventory.isAvailable.mockResolvedValue(true);
    prisma.inventory.updateMany.mockResolvedValue({ count: 1 });
    txMock.inventory.updateMany.mockResolvedValue({ count: 1 });
    txMock.order.create.mockImplementation((args: { data: { number: string } }) =>
      Promise.resolve({ id: 'o-1', number: args.data.number } as never),
    );
    txMock.cartItem.deleteMany.mockResolvedValue({ count: 1 });

    const result = await service.createFromCart('user-1');

    expect(result.order).toBeDefined();
    expect(prisma.$transaction).toHaveBeenCalled();
    expect(txMock.inventory.updateMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { productId: 'p-1', quantity: { gte: 2 } },
      }),
    );
  });

  it('forbids reading another user order', async () => {
    orderRepository.findById.mockResolvedValue({
      id: 'o-1',
      userId: 'someone-else',
    } as never);

    await expect(service.getById('user-1', 'o-1')).rejects.toThrow(
      'Order does not belong to this user',
    );
  });
});
