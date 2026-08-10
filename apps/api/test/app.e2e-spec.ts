import { Test } from '@nestjs/testing';
import { INestApplication, ValidationPipe, VersioningType } from '@nestjs/common';
import request from 'supertest';
import { randomUUID } from 'crypto';
import { AppModule } from '../src/app.module';
import { AllExceptionsFilter } from '../src/common/filters/all-exceptions.filter';

/**
 * End-to-end commerce flow:
 * register → login → browse products → cart → order → order status.
 * Requires a running PostgreSQL (see docker-compose).
 */
describe('Commerce API (e2e)', () => {
  let app: INestApplication;
  let token: string;
  const email = `e2e-${randomUUID()}@commerce.ai`;
  const password = 'e2e-password-123';

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleRef.createNestApplication();
    app.setGlobalPrefix('api');
    app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' });
    app.useGlobalPipes(
      new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true }),
    );
    app.useGlobalFilters(new AllExceptionsFilter());
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('GET /api/v1/health returns ok', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/health').expect(200);
    expect(res.body.status).toBe('ok');
  });

  it('registers and logs in', async () => {
    await request(app.getHttpServer())
      .post('/api/v1/auth/register')
      .send({ email, name: 'E2E User', password })
      .expect(201);

    const login = await request(app.getHttpServer())
      .post('/api/v1/auth/login')
      .send({ email, password })
      .expect(200);

    expect(login.body.accessToken).toBeDefined();
    token = login.body.accessToken as string;
  });

  it('GET /api/v1/products returns seeded products with pagination', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/products').expect(200);

    expect(res.body.total).toBeGreaterThan(50);
    expect(res.body.items.length).toBeLessThanOrEqual(20);
    expect(res.body.items[0]).toHaveProperty('sku');
  });

  it('filters products by category and max price', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/v1/products')
      .query({ category: 'notebooks', maxPriceCents: 500000 })
      .expect(200);

    const notebooks = res.body.items as Array<{
      category: { slug: string };
      priceCents: number;
    }>;
    expect(notebooks.length).toBeGreaterThan(0);
    for (const n of notebooks) {
      expect(n.category.slug).toBe('notebooks');
      expect(n.priceCents).toBeLessThanOrEqual(500000);
    }
  });

  it('returns inventory for a product', async () => {
    const products = await request(app.getHttpServer())
      .get('/api/v1/products')
      .expect(200);
    const productId = (products.body.items[0] as { id: string }).id;

    const res = await request(app.getHttpServer())
      .get(`/api/v1/products/${productId}/inventory`)
      .expect(200);

    expect(res.body).toHaveProperty('available');
    expect(res.body).toHaveProperty('inStock');
  });

  it('rejects unauthenticated cart access', async () => {
    await request(app.getHttpServer()).get('/api/v1/cart').expect(401);
  });

  it('adds to cart, creates order, and reads order status', async () => {
    const products = await request(app.getHttpServer())
      .get('/api/v1/products')
      .query({ category: 'notebooks' })
      .expect(200);
    const productId = (products.body.items[0] as { id: string }).id;

    const cart = await request(app.getHttpServer())
      .post('/api/v1/cart/items')
      .set('Authorization', `Bearer ${token}`)
      .send({ productId, quantity: 1 })
      .expect(201);

    expect(cart.body.subtotalCents).toBeGreaterThan(0);

    const order = await request(app.getHttpServer())
      .post('/api/v1/orders')
      .set('Authorization', `Bearer ${token}`)
      .expect(201);

    expect(order.body.order.number).toMatch(/^ORD-/);
    expect(order.body.order.status).toBe('PENDING');

    const orderNumber = (order.body.order as { number: string }).number;
    const status = await request(app.getHttpServer())
      .get(`/api/v1/orders/by-number/${orderNumber}`)
      .set('Authorization', `Bearer ${token}`)
      .expect(200);

    expect(status.body.status).toBe('PENDING');
    expect(status.body.totalCents).toBeGreaterThan(0);
  });

  it('validates DTOs and rejects unknown fields', async () => {
    await request(app.getHttpServer())
      .post('/api/v1/auth/login')
      .send({ email: 'not-an-email', password: 'x', extra: true })
      .expect(400);
  });
});
