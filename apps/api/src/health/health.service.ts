import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from '../common/prisma/prisma.service';
import Redis from 'ioredis';

@Injectable()
export class HealthService {
  private readonly logger = new Logger(HealthService.name);
  private readonly redis: Redis | null;

  constructor(
    private readonly prisma: PrismaService,
    config: ConfigService,
  ) {
    const url = config.get<string>('REDIS_URL');
    if (url) {
      this.redis = new Redis(url, {
        lazyConnect: true,
        maxRetriesPerRequest: 1,
        retryStrategy: () => null,
      });
    } else {
      this.redis = null;
    }
  }

  async check(): Promise<Record<string, unknown>> {
    const checks: Record<string, string> = {};

    checks.database = await this.ping('database', () => this.prisma.$queryRaw`SELECT 1`);
    checks.redis = await this.ping('redis', async () => {
      if (!this.redis) return;
      await this.redis.connect().catch(() => undefined);
      await this.redis.ping();
    });

    const degraded = Object.values(checks).some((v) => v !== 'up');
    return {
      status: degraded ? 'degraded' : 'ok',
      checks,
      timestamp: new Date().toISOString(),
    };
  }

  private async ping(name: string, fn: () => Promise<unknown>): Promise<string> {
    try {
      await fn();
      return 'up';
    } catch (err) {
      this.logger.warn(`Health check "${name}" failed: ${String(err)}`);
      return 'down';
    }
  }

  async onModuleDestroy(): Promise<void> {
    await this.redis?.disconnect();
  }
}
