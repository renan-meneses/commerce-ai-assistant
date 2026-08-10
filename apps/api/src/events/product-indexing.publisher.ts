import { Injectable, Logger } from '@nestjs/common';
import { ProductDomainEvent } from '../products/products.service';
import { INDEXING_EXCHANGE, RabbitMqPublisher } from './rabbitmq.publisher';

/**
 * Publishes product lifecycle events consumed by the AI indexing worker.
 * A no-op fallback is used in test environments where RabbitMQ is absent,
 * keeping the API fully usable for local development and CI.
 */
@Injectable()
export class ProductIndexingPublisher {
  private readonly logger = new Logger(ProductIndexingPublisher.name);

  constructor(private readonly rabbit: RabbitMqPublisher) {}

  async publish(event: ProductDomainEvent): Promise<void> {
    try {
      await this.rabbit.publish(INDEXING_EXCHANGE, `product.${event.type}`, event);
    } catch (err) {
      this.logger.error(
        `Failed to publish indexing event for ${event.productId}: ${String(err)}`,
      );
    }
  }
}
