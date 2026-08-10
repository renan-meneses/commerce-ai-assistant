import { Module } from '@nestjs/common';
import { EventsModule } from '../events/events.module';
import { InventoryModule } from '../inventory/inventory.module';
import { ProductInventoryController } from './product-inventory.controller';
import { ProductsController } from './products.controller';
import { ProductsService } from './products.service';
import { PRODUCT_REPOSITORY } from './domain/product.repository';
import { PrismaProductRepository } from './infrastructure/prisma-product.repository';

@Module({
  imports: [EventsModule, InventoryModule],
  controllers: [ProductsController, ProductInventoryController],
  providers: [
    ProductsService,
    {
      provide: PRODUCT_REPOSITORY,
      useClass: PrismaProductRepository,
    },
  ],
  exports: [ProductsService],
})
export class ProductsModule {}
