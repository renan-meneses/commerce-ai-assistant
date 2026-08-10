import { Body, Controller, HttpCode, HttpStatus, Post } from '@nestjs/common';
import { ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import { CurrentUser } from '../common/decorators/current-user.decorator';
import { AiService, ChatResponse } from './ai.service';
import { ChatRequestDto } from './dto/chat.dto';

@ApiTags('ai')
@Controller('ai')
export class AiController {
  constructor(private readonly aiService: AiService) {}

  @Post('chat')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    summary: 'Chat with the AI shopping assistant (RAG + tools, routed by LangGraph)',
    description:
      'Knowledge questions (specs, comparisons) are answered via RAG; ' +
      'real-time questions (price, stock, order status) call controlled tools.',
  })
  @ApiOkResponse({
    schema: {
      example: {
        answer: 'The ASUS Vivobook 16X (R$4.899) is well suited...',
        intent: 'PRODUCT_RECOMMENDATION',
        sources: [{ productId: 'uuid', score: 0.87 }],
        toolResults: [],
      },
    },
  })
  async chat(
    @Body() dto: ChatRequestDto,
    @CurrentUser('id') userId?: string,
  ): Promise<ChatResponse> {
    return this.aiService.chat({
      ...dto,
      userId: dto.userId ?? userId,
    });
  }
}
