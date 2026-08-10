import { ConflictException, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { AuthService } from './auth.service';
import { PrismaService } from '../common/prisma/prisma.service';

describe('AuthService', () => {
  let service: AuthService;
  const prisma = {
    user: {
      findUnique: jest.fn(),
      create: jest.fn(),
    },
  };
  const jwt = {
    sign: jest.fn().mockReturnValue('signed-token'),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    const config = new ConfigService({ JWT_SECRET: 'test', JWT_EXPIRES_IN: '1h' });
    service = new AuthService(
      prisma as unknown as PrismaService,
      jwt as unknown as JwtService,
      config,
    );
  });

  it('rejects duplicate email registration', async () => {
    prisma.user.findUnique.mockResolvedValue({ id: 'u-1' });

    await expect(
      service.register({ email: 'a@b.com', name: 'A', password: '12345678' }),
    ).rejects.toThrow(ConflictException);
  });

  it('rejects invalid credentials', async () => {
    prisma.user.findUnique.mockResolvedValue(null);

    await expect(service.login({ email: 'a@b.com', password: 'wrong' })).rejects.toThrow(
      UnauthorizedException,
    );
  });

  it('returns a token for valid login', async () => {
    prisma.user.findUnique.mockResolvedValue({
      id: 'u-1',
      email: 'a@b.com',
      name: 'A',
      role: 'CUSTOMER',
      passwordHash: '$2a$12$cKb4ScNmYVw7kSkApTL7D.5PVOOSPkBSfjThkYx3z14CwyVZamD.C',
    });

    const result = await service.login({ email: 'a@b.com', password: '12345678' });

    expect(result.accessToken).toBe('signed-token');
    expect(jwt.sign).toHaveBeenCalled();
  });
});
