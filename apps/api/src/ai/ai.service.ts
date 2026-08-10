import { Injectable, Logger, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
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
 * ID and a short-lived scoped service token so the agent can call
 * user-scoped tools (e.g. order status) on the caller's behalf. The
 * backend still enforces ownership — the token only identifies the user.
 */
@Injectable()
export class AiService {
  private readonly logger = new Logger(AiService.name);
  private readonly baseUrl: string;
  private readonly jwtSecret: string;

  constructor(
    config: ConfigService,
    private readonly jwt: JwtService,
  ) {
    this.baseUrl = config.get<string>('AI_SERVICE_URL') ?? 'http://ai-service:8000';
    this.jwtSecret = config.get<string>('JWT_SECRET') ?? 'dev-secret';
  }

  async chat(dto: ChatRequestDto): Promise<ChatResponse> {
    const correlationId = dto.correlationId ?? randomUUID();
    const serviceToken = dto.userId
      ? this.jwt.sign(
          { sub: dto.userId, aud: 'ai-service', scope: 'agent' },
          { secret: this.jwtSecret, expiresIn: '5m' },
        )
      : undefined;
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/ai/chat`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-request-id': correlationId,
          ...(serviceToken ? { 'x-service-token': serviceToken } : {}),
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
