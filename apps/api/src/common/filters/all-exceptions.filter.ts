import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { randomUUID } from 'crypto';
import { Request, Response } from 'express';

/**
 * Centralized error handling.
 *
 * - Maps known exceptions (HttpException, Prisma errors) to a consistent
 *   JSON error envelope: { statusCode, message, error, requestId }.
 * - Never leaks stack traces or internal details to clients.
 * - Prisma unique-constraint violations become 409s instead of 500s.
 */
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger(AllExceptionsFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
    const requestId = (request.headers['x-request-id'] as string) ?? randomUUID();

    let statusCode: number;
    let message: string | string[];
    let error: string;

    if (exception instanceof HttpException) {
      statusCode = exception.getStatus();
      const body = exception.getResponse();
      if (typeof body === 'string') {
        message = body;
        error = exception.name;
      } else if (typeof body === 'object' && body !== null) {
        const b = body as Record<string, unknown>;
        message = (b.message as string | string[]) ?? exception.message;
        error = (b.error as string) ?? exception.name;
      } else {
        message = exception.message;
        error = exception.name;
      }
    } else if (exception instanceof Prisma.PrismaClientKnownRequestError) {
      if (exception.code === 'P2002') {
        statusCode = HttpStatus.CONFLICT;
        message = 'Resource already exists (unique constraint violation)';
        error = 'Conflict';
      } else if (exception.code === 'P2025') {
        statusCode = HttpStatus.NOT_FOUND;
        message = 'Resource not found';
        error = 'NotFound';
      } else {
        statusCode = HttpStatus.INTERNAL_SERVER_ERROR;
        message = 'Database error';
        error = 'DatabaseError';
      }
    } else {
      statusCode = HttpStatus.INTERNAL_SERVER_ERROR;
      message = 'Internal server error';
      error = 'InternalServerError';
    }

    if (statusCode >= 500) {
      this.logger.error(
        `${request.method} ${request.url} failed: ${
          exception instanceof Error ? exception.stack : String(exception)
        }`,
      );
    }

    response.status(statusCode).json({
      statusCode,
      message,
      error,
      requestId,
      path: request.url,
      timestamp: new Date().toISOString(),
    });
  }
}
