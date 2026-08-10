import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  UseGuards,
} from '@nestjs/common';
import { ApiBearerAuth, ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import { User } from '@prisma/client';
import { CurrentUser } from '../common/decorators/current-user.decorator';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CartService, CartView } from './cart.service';
import { AddCartItemDto, UpdateCartItemDto } from './dto/cart.dto';

@ApiTags('cart')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('cart')
export class CartController {
  constructor(private readonly cartService: CartService) {}

  @Get()
  @ApiOperation({ summary: 'View the current cart with live prices' })
  @ApiOkResponse({ type: Object })
  view(@CurrentUser('id') userId: string): Promise<CartView> {
    return this.cartService.view(userId);
  }

  @Post('items')
  @ApiOperation({ summary: 'Add an item to the cart (checks availability)' })
  @ApiOkResponse({ type: Object })
  addItem(
    @CurrentUser('id') userId: string,
    @Body() dto: AddCartItemDto,
  ): Promise<CartView> {
    return this.cartService.addItem(userId, dto);
  }

  @Patch('items/:productId')
  @ApiOperation({ summary: 'Update the quantity of a cart item' })
  @ApiOkResponse({ type: Object })
  updateItem(
    @CurrentUser('id') userId: string,
    @Param('productId', ParseUUIDPipe) productId: string,
    @Body() dto: UpdateCartItemDto,
  ): Promise<CartView> {
    return this.cartService.updateItem(userId, productId, dto.quantity);
  }

  @Delete('items/:productId')
  @ApiOperation({ summary: 'Remove an item from the cart' })
  @ApiOkResponse({ type: Object })
  removeItem(
    @CurrentUser('id') userId: string,
    @Param('productId', ParseUUIDPipe) productId: string,
  ): Promise<CartView> {
    return this.cartService.removeItem(userId, productId);
  }

  @Delete()
  @ApiOperation({ summary: 'Clear the cart' })
  async clear(@CurrentUser('id') userId: string): Promise<{ cleared: boolean }> {
    await this.cartService.clear(userId);
    return { cleared: true };
  }
}
