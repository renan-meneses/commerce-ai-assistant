import { Injectable, Logger, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { randomUUID } from 'crypto';
import { ChatRequestDto } from './dto/chat.dto';

export interface ChatResponse {
  answer: string;
  intent: string;
  sources: unknown[];
  toolResults: unknown[];
  traceId?: string;
}

/**
 * AI assistant gateway.
 *
 * The NestJS API does not talk to LLMs itself. It forwards validated
 * chat requests to the FastAPI AI service, propagating the correlation
 * ID and the authenticated user id (when available) so the agent can
 * call user-scoped tools (e.g. order status) on the caller's behalf.
 */
@Injectable()
export class AiService {
  private readonly logger = new Logger(AiService.name);
  private readonly baseUrl: string;

  constructor(config: ConfigService) {
    this.baseUrl = config.get<string>('AI_SERVICE_URL') ?? 'http://ai-service:8000';
  }

  async chat(dto: ChatRequestDto): Promise<ChatResponse> {
    const correlationId = dto.correlationId ?? randomUUID();
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/ai/chat`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-request-id': correlationId,
        },
        body: JSON.stringify({
          messages: dto.messages,
          user_id: dto.userId,
          correlation_id: correlationId,
        }),
        signal: AbortSignal.timeout(45_000),
      });

      if (!response.ok) {
        this.logger.error(
          `AI service responded ${response.status} for request ${correlationId}`,
        );
        throw new ServiceUnavailableException(
          `AI service unavailable (${response.status})`,
        );
      }

      return (await response.json()) as ChatResponse;
    } catch (err) {
      if (err instanceof ServiceUnavailableException) throw err;
      this.logger.error(`AI service call failed: ${String(err)}`);
      throw new ServiceUnavailableException('AI service unavailable');
    }
  }
}
