import { NestFactory } from '@nestjs/core';
import { ValidationPipe, VersioningType } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { Logger } from 'nestjs-pino';
import helmet from 'helmet';
import { AppModule } from './app.module';
import { AllExceptionsFilter } from './common/filters/all-exceptions.filter';
import { CorrelationIdInterceptor } from './common/interceptors/correlation-id.interceptor';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, { bufferLogs: true });

  app.useLogger(app.get(Logger));
  app.use(helmet());
  app.enableCors({ origin: process.env.CORS_ORIGIN?.split(',') ?? true });

  app.setGlobalPrefix('api');
  app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' });

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );
  app.useGlobalFilters(new AllExceptionsFilter());
  app.useGlobalInterceptors(new CorrelationIdInterceptor());

  const swaggerConfig = new DocumentBuilder()
    .setTitle('commerce-ai-assistant API')
    .setDescription(
      'E-commerce API with an AI shopping assistant. ' +
        'The assistant is served through POST /api/v1/ai/chat, which forwards ' +
        'requests to the FastAPI AI service (LangGraph + RAG).',
    )
    .setVersion('1.0')
    .addBearerAuth()
    .addTag('auth', 'Authentication and user registration')
    .addTag('products', 'Product catalog')
    .addTag('inventory', 'Stock and availability')
    .addTag('cart', 'Shopping cart')
    .addTag('orders', 'Orders and order status')
    .addTag('ai', 'AI shopping assistant')
    .addTag('health', 'Liveness and readiness')
    .build();
  const document = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('docs', app, document, {
    swaggerOptions: { persistAuthorization: true },
  });

  const port = Number(process.env.API_PORT ?? 3000);
  await app.listen(port);
  Logger.prototype.log(`API listening on http://localhost:${port} — Swagger at /docs`);
}

void bootstrap();
