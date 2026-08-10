import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  ArrayMaxSize,
  IsArray,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
} from 'class-validator';

export class ChatMessageDto {
  @ApiProperty({ enum: ['user', 'assistant'], example: 'user' })
  @IsString()
  role!: 'user' | 'assistant';

  @ApiProperty({ example: 'I need a notebook under R$5.000 for Python development' })
  @IsString()
  @MaxLength(4000)
  content!: string;
}

export class ChatRequestDto {
  @ApiProperty({ type: [ChatMessageDto], description: 'Conversation history' })
  @IsArray()
  @ArrayMaxSize(20)
  messages!: ChatMessageDto[];

  @ApiPropertyOptional({
    description: 'When provided, tools operate in the caller context (orders, cart).',
    example: 'b3d7a7f2-...',
  })
  @IsOptional()
  @IsUUID()
  userId?: string;

  @ApiPropertyOptional({
    description: 'Correlation ID propagated to the AI service.',
    example: 'c1f8...',
  })
  @IsOptional()
  @IsString()
  correlationId?: string;
}
