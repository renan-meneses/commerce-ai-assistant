import { Controller, Get } from '@nestjs/common';
import { ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import { HealthService } from './health.service';

@ApiTags('health')
@Controller('health')
export class HealthController {
  constructor(private readonly healthService: HealthService) {}

  @Get()
  @ApiOperation({ summary: 'Liveness + readiness check' })
  @ApiOkResponse({
    schema: {
      example: {
        status: 'ok',
        checks: { database: 'up', redis: 'up', rabbitmq: 'up' },
        timestamp: '2026-01-01T00:00:00.000Z',
      },
    },
  })
  check(): Promise<Record<string, unknown>> {
    return this.healthService.check();
  }
}
