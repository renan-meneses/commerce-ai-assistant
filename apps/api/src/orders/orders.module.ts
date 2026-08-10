import { Module } from '@nestjs/common';
import { InventoryModule } from '../inventory/inventory.module';
import { CartModule } from '../cart/cart.module';
import { OrdersController } from './orders.controller';
import { OrdersService } from './orders.service';
import { ORDER_REPOSITORY } from './domain/order.repository';
import { PrismaOrderRepository } from './infrastructure/prisma-order.repository';
import { CART_REPOSITORY } from '../cart/domain/cart.repository';
import { PrismaCartRepository } from '../cart/infrastructure/prisma-cart.repository';

@Module({
  imports: [InventoryModule, CartModule],
  controllers: [OrdersController],
  providers: [
    OrdersService,
    {
      provide: ORDER_REPOSITORY,
      useClass: PrismaOrderRepository,
    },
    {
      provide: CART_REPOSITORY,
      useClass: PrismaCartRepository,
    },
  ],
  exports: [OrdersService],
})
export class OrdersModule {}
