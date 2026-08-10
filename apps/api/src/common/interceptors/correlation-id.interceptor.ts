import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { randomUUID } from 'crypto';
import { Request, Response } from 'express';

const CORRELATION_ID_HEADER = 'x-request-id';

/**
 * Correlation ID propagation.
 *
 * Accepts an inbound `x-request-id` when present, otherwise generates one.
 * The same id is echoed in the response and propagated to downstream
 * services (FastAPI AI service, LLM providers, queues) so that a single
 * user request is traceable across the whole system.
 */
@Injectable()
export class CorrelationIdInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const ctx = context.switchToHttp();
    const request = ctx.getRequest<Request>();
    const response = ctx.getResponse<Response>();

    const incoming = request.headers[CORRELATION_ID_HEADER];
    const correlationId = Array.isArray(incoming)
      ? incoming[0]
      : (incoming ?? randomUUID());

    request.headers[CORRELATION_ID_HEADER] = correlationId;
    response.setHeader(CORRELATION_ID_HEADER, correlationId);
    (request as Request & { correlationId?: string }).correlationId = correlationId;

    return next.handle();
  }
}
