import { Module } from '@nestjs/common';
import { InventoryModule } from '../inventory/inventory.module';
import { CartController } from './cart.controller';
import { CartService } from './cart.service';
import { CART_REPOSITORY } from './domain/cart.repository';
import { PrismaCartRepository } from './infrastructure/prisma-cart.repository';

@Module({
  imports: [InventoryModule],
  controllers: [CartController],
  providers: [
    CartService,
    {
      provide: CART_REPOSITORY,
      useClass: PrismaCartRepository,
    },
  ],
  exports: [CartService],
})
export class CartModule {}
