import { Module } from '@nestjs/common';
import { ProductIndexingPublisher } from './product-indexing.publisher';
import { RabbitMqPublisher } from './rabbitmq.publisher';

@Module({
  providers: [RabbitMqPublisher, ProductIndexingPublisher],
  exports: [ProductIndexingPublisher],
})
export class EventsModule {}
