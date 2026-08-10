import { Injectable, OnModuleDestroy, OnModuleInit, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as amqp from 'amqplib';

export const INDEXING_EXCHANGE = 'commerce.product';
export const INDEXING_QUEUE = 'commerce.indexing.product';

/**
 * RabbitMQ connection wrapper.
 *
 * Publishes product events to an exchange with a durable queue bound to
 * it. The queue is configured with a dead-letter exchange so failed
 * messages can be retried/diagnosed (see docs/rag-architecture.md).
 *
 * The publisher interface is intentionally minimal so a future Kafka
 * implementation could be swapped in (ADR-006).
 */
@Injectable()
export class RabbitMqPublisher implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(RabbitMqPublisher.name);
  private connection: amqp.ChannelModel | null = null;
  private channel: amqp.Channel | null = null;
  private readonly url: string;

  constructor(config: ConfigService) {
    this.url =
      config.get<string>('RABBITMQ_URL') ??
      'amqp://commerce:commerce_dev_password@rabbitmq:5672';
  }

  async onModuleInit(): Promise<void> {
    if (!process.env.RABBITMQ_URL && process.env.NODE_ENV === 'test') {
      this.logger.warn('RabbitMQ disabled in test environment');
      return;
    }
    try {
      await this.connect();
    } catch (err) {
      this.logger.error(`RabbitMQ connection failed: ${String(err)}`);
    }
  }

  private async connect(): Promise<void> {
    this.connection = await amqp.connect(this.url, { heartbeat: 30 });
    this.channel = await this.connection.createChannel();
    await this.channel.assertExchange(INDEXING_EXCHANGE, 'topic', { durable: true });
    await this.channel.assertQueue(INDEXING_QUEUE, {
      durable: true,
      arguments: {
        'x-dead-letter-exchange': 'commerce.product.dlx',
      },
    });
    await this.channel.assertExchange('commerce.product.dlx', 'topic', {
      durable: true,
    });
    await this.channel.bindQueue(INDEXING_QUEUE, INDEXING_EXCHANGE, 'product.*');
    this.connection.on('error', (err) =>
      this.logger.error(`RabbitMQ connection error: ${String(err)}`),
    );
  }

  async publish(exchange: string, routingKey: string, message: object): Promise<void> {
    if (!this.channel) {
      await this.connect();
    }
    if (!this.channel) {
      throw new Error('RabbitMQ channel unavailable');
    }
    this.channel.publish(exchange, routingKey, Buffer.from(JSON.stringify(message)), {
      persistent: true,
    });
  }

  async onModuleDestroy(): Promise<void> {
    await this.channel?.close().catch(() => undefined);
    await this.connection?.close().catch(() => undefined);
  }
}
