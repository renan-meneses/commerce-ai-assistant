import {
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  Query,
} from '@nestjs/common';
import {
  ApiCreatedResponse,
  ApiOkResponse,
  ApiOperation,
  ApiTags,
} from '@nestjs/swagger';
import { Product } from '@prisma/client';
import { ProductsService } from './products.service';
import { CreateProductDto, ListProductsQuery, UpdateProductDto } from './dto/product.dto';
import { ProductIndexingPublisher } from '../events/product-indexing.publisher';

@ApiTags('products')
@Controller('products')
export class ProductsController {
  constructor(
    private readonly productsService: ProductsService,
    private readonly indexingPublisher: ProductIndexingPublisher,
  ) {}

  @Get()
  @ApiOperation({ summary: 'List products with filters, pagination and sorting' })
  @ApiOkResponse({
    schema: {
      example: {
        items: [
          {
            id: 'uuid',
            sku: 'NB-ASUS-VIVO-16',
            name: 'ASUS Vivobook 16X',
            priceCents: 489900,
          },
        ],
        total: 60,
        page: 1,
        limit: 20,
        pages: 3,
      },
    },
  })
  findAll(@Query() query: ListProductsQuery): Promise<unknown> {
    return this.productsService.findAll(query);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get a product by id (includes category and inventory)' })
  @ApiOkResponse({ type: Object })
  findOne(@Param('id', ParseUUIDPipe) id: string): Promise<Product> {
    return this.productsService.findOne(id);
  }

  @Post()
  @ApiOperation({ summary: 'Create a product and enqueue async AI indexing' })
  @ApiCreatedResponse({ type: Object })
  async create(@Body() dto: CreateProductDto): Promise<Product> {
    const product = await this.productsService.create(dto);
    const event = await this.productsService.buildEvent(product);
    await this.indexingPublisher.publish(event);
    return product;
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update a product and enqueue async AI re-indexing' })
  @ApiOkResponse({ type: Object })
  async update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateProductDto,
  ): Promise<Product> {
    const product = await this.productsService.update(id, dto);
    const event = await this.productsService.buildEvent(product);
    await this.indexingPublisher.publish(event);
    return product;
  }
}
