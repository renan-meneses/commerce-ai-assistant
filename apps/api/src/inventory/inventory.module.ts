import { Module } from '@nestjs/common';
import { InventoryController } from './inventory.controller';
import { InventoryService } from './inventory.service';
import { INVENTORY_REPOSITORY } from './domain/inventory.repository';
import { PrismaInventoryRepository } from './infrastructure/prisma-inventory.repository';

@Module({
  controllers: [InventoryController],
  providers: [
    InventoryService,
    {
      provide: INVENTORY_REPOSITORY,
      useClass: PrismaInventoryRepository,
    },
  ],
  exports: [InventoryService],
})
export class InventoryModule {}
