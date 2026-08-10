import { ServiceUnavailableException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { AiService } from './ai.service';

describe('AiService', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  function buildService() {
    const jwt = new JwtService({});
    const config = new ConfigService({ JWT_SECRET: 'test-secret' });
    return new AiService(config, jwt);
  }

  it('mints a scoped service token and forwards it to the AI service', async () => {
    const service = buildService();
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        answer: 'ok',
        intent: 'PRODUCT_SEARCH',
        sources: [],
        toolResults: [],
      }),
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    await service.chat({
      messages: [{ role: 'user', content: 'hello' }],
      userId: 'user-123',
    });

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Record<string, string>;
    expect(headers['x-service-token']).toBeDefined();

    const payload = JSON.parse(init.body as string) as { user_id: string };
    expect(payload.user_id).toBe('user-123');
  });

  it('skips the service token when no user is authenticated', async () => {
    const service = buildService();
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        answer: 'ok',
        intent: 'GENERAL_KNOWLEDGE',
        sources: [],
        toolResults: [],
      }),
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    await service.chat({ messages: [{ role: 'user', content: 'hello' }] });

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Record<string, string>;
    expect(headers['x-service-token']).toBeUndefined();
  });

  it('surfaces AI service failures as 503', async () => {
    const service = buildService();
    const fetchMock = jest.fn().mockResolvedValue({ ok: false, status: 500 });
    global.fetch = fetchMock as unknown as typeof fetch;

    await expect(
      service.chat({ messages: [{ role: 'user', content: 'hello' }] }),
    ).rejects.toThrow(ServiceUnavailableException);
  });
});
