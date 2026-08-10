import { Controller, Get, Param, ParseUUIDPipe, Patch, Query } from '@nestjs/common';
import { ApiOkResponse, ApiOperation, ApiQuery, ApiTags } from '@nestjs/swagger';
import { InventoryService } from './inventory.service';

@ApiTags('inventory')
@Controller('inventory')
export class InventoryController {
  constructor(private readonly inventoryService: InventoryService) {}

  @Get('low')
  @ApiOperation({ summary: 'List low-stock products' })
  @ApiQuery({ name: 'threshold', required: false, example: 5 })
  lowStock(@Query('threshold') threshold?: number): Promise<unknown[]> {
    return this.inventoryService.lowStock(threshold ?? 5);
  }

  @Patch('restock/:productId')
  @ApiOperation({ summary: 'Increase stock for a product' })
  @ApiOkResponse({ type: Object })
  restock(
    @Param('productId', ParseUUIDPipe) productId: string,
    @Query('delta') delta: number,
  ): Promise<unknown> {
    return this.inventoryService.restock(productId, Number(delta));
  }
}
