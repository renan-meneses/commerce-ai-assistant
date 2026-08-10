import { ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import { Controller, Get, NotFoundException, Param, ParseUUIDPipe } from '@nestjs/common';
import { InventoryService } from '../inventory/inventory.service';
import { ProductsService } from './products.service';

@ApiTags('inventory')
@Controller('products')
export class ProductInventoryController {
  constructor(
    private readonly productsService: ProductsService,
    private readonly inventoryService: InventoryService,
  ) {}

  @Get(':id/inventory')
  @ApiOperation({ summary: 'Get live stock availability for a product' })
  @ApiOkResponse({
    schema: {
      example: {
        productId: 'uuid',
        quantity: 14,
        reserved: 2,
        available: 12,
        inStock: true,
      },
    },
  })
  async inventory(@Param('id', ParseUUIDPipe) id: string): Promise<unknown> {
    const product = await this.productsService.findOne(id);
    if (!product) {
      throw new NotFoundException(`Product ${id} not found`);
    }
    const entry = await this.inventoryService.getByProduct(id);
    return { ...entry, inStock: entry.available > 0 };
  }
}
