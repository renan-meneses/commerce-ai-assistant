import { Body, Controller, Get, Param, Post, UseGuards } from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiCreatedResponse,
  ApiOkResponse,
  ApiOperation,
  ApiTags,
} from '@nestjs/swagger';
import { Order, OrderStatus } from '@prisma/client';
import { CurrentUser } from '../common/decorators/current-user.decorator';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { OrdersService } from './orders.service';
import { UpdateOrderStatusDto } from './dto/update-order-status.dto';

@ApiTags('orders')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('orders')
export class OrdersController {
  constructor(private readonly ordersService: OrdersService) {}

  @Post()
  @ApiOperation({ summary: 'Create an order from the current cart (transactional)' })
  @ApiCreatedResponse({
    schema: {
      example: {
        order: {
          id: 'uuid',
          number: 'ORD-20260101-ABC123',
          status: 'PENDING',
          totalCents: 489900,
        },
        reserved: true,
      },
    },
  })
  createFromCart(@CurrentUser('id') userId: string): Promise<unknown> {
    return this.ordersService.createFromCart(userId);
  }

  @Get()
  @ApiOperation({ summary: 'List the authenticated user orders' })
  @ApiOkResponse({ type: Object, isArray: true })
  listForUser(@CurrentUser('id') userId: string): Promise<Order[]> {
    return this.ordersService.listForUser(userId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get an order by id (own orders only)' })
  @ApiOkResponse({ type: Object })
  getById(@CurrentUser('id') userId: string, @Param('id') id: string): Promise<Order> {
    return this.ordersService.getById(userId, id);
  }

  @Get('by-number/:number')
  @ApiOperation({ summary: 'Get an order by order number, e.g. ORD-20260101-ABC123' })
  @ApiOkResponse({ type: Object })
  getByNumber(
    @CurrentUser('id') userId: string,
    @Param('number') number: string,
  ): Promise<unknown> {
    return this.ordersService.getStatusForAssistant(userId, number);
  }

  @Post(':id/status')
  @ApiOperation({ summary: 'Update order status (admin simulation)' })
  @ApiOkResponse({ type: Object })
  updateStatus(
    @Param('id') id: string,
    @Body() dto: UpdateOrderStatusDto,
  ): Promise<Order> {
    return this.ordersService.updateStatus(id, dto.status as OrderStatus);
  }
}
