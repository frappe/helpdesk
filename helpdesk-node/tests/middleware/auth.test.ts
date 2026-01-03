import { describe, it, expect, vi } from 'vitest';
import { authenticate, authorize } from '../../src/middleware/auth.js';
import { generateToken } from '../../src/utils/jwt.js';
import { Request, Response, NextFunction } from 'express';
import { createUser } from '../factories/userFactory.js';

describe('Auth Middleware', () => {
  describe('authenticate', () => {
    it('should authenticate valid token', async () => {
      const { user } = await createUser();
      const token = generateToken({ userId: user.id, userType: user.userType });

      const req = {
        headers: {
          authorization: `Bearer ${token}`,
        },
        user: undefined,
      } as unknown as Request;

      const res = {} as Response;
      const next = vi.fn() as NextFunction;

      await authenticate(req, res, next);

      expect(req.user).toBeDefined();
      expect(req.user?.userId).toBe(user.id);
      expect(req.user?.userType).toBe(user.userType);
      expect(next).toHaveBeenCalledWith();
    });

    it('should reject request without authorization header', async () => {
      const req = {
        headers: {},
      } as Request;

      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn(),
      } as unknown as Response;

      const next = vi.fn() as NextFunction;

      await authenticate(req, res, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(res.json).toHaveBeenCalledWith({
        status: 'error',
        message: 'No token provided',
      });
      expect(next).not.toHaveBeenCalled();
    });

    it('should reject request with invalid token format', async () => {
      const req = {
        headers: {
          authorization: 'InvalidFormat token123',
        },
      } as Request;

      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn(),
      } as unknown as Response;

      const next = vi.fn() as NextFunction;

      await authenticate(req, res, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(next).not.toHaveBeenCalled();
    });

    it('should reject request with invalid token', async () => {
      const req = {
        headers: {
          authorization: 'Bearer invalid-token-string',
        },
      } as Request;

      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn(),
      } as unknown as Response;

      const next = vi.fn() as NextFunction;

      await authenticate(req, res, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(res.json).toHaveBeenCalledWith({
        status: 'error',
        message: 'Invalid token',
      });
      expect(next).not.toHaveBeenCalled();
    });

    it('should reject expired token', async () => {
      const { user } = await createUser();
      // Generate token with past expiration
      const expiredToken = generateToken(
        { userId: user.id, userType: user.userType },
        '0s' // Expire immediately
      );

      // Wait a bit to ensure it's expired
      await new Promise((resolve) => setTimeout(resolve, 100));

      const req = {
        headers: {
          authorization: `Bearer ${expiredToken}`,
        },
      } as Request;

      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn(),
      } as unknown as Response;

      const next = vi.fn() as NextFunction;

      await authenticate(req, res, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(next).not.toHaveBeenCalled();
    });
  });

  describe('authorize', () => {
    it('should authorize user with allowed role', async () => {
      const { user } = await createUser({ userType: 'AGENT' });
      const token = generateToken({ userId: user.id, userType: user.userType });

      const req = {
        headers: {
          authorization: `Bearer ${token}`,
        },
        user: {
          userId: user.id,
          userType: 'AGENT',
        },
      } as unknown as Request;

      const res = {} as Response;
      const next = vi.fn() as NextFunction;

      const middleware = authorize(['AGENT', 'ADMIN']);
      middleware(req, res, next);

      expect(next).toHaveBeenCalledWith();
    });

    it('should reject user with unauthorized role', async () => {
      const { user } = await createUser({ userType: 'CUSTOMER' });

      const req = {
        user: {
          userId: user.id,
          userType: 'CUSTOMER',
        },
      } as unknown as Request;

      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn(),
      } as unknown as Response;

      const next = vi.fn() as NextFunction;

      const middleware = authorize(['AGENT', 'ADMIN']);
      middleware(req, res, next);

      expect(res.status).toHaveBeenCalledWith(403);
      expect(res.json).toHaveBeenCalledWith({
        status: 'error',
        message: 'Insufficient permissions',
      });
      expect(next).not.toHaveBeenCalled();
    });

    it('should reject request without user', async () => {
      const req = {} as Request;

      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn(),
      } as unknown as Response;

      const next = vi.fn() as NextFunction;

      const middleware = authorize(['AGENT']);
      middleware(req, res, next);

      expect(res.status).toHaveBeenCalledWith(403);
      expect(next).not.toHaveBeenCalled();
    });

    it('should allow ADMIN to access all endpoints', async () => {
      const { user } = await createUser({ userType: 'ADMIN' });

      const req = {
        user: {
          userId: user.id,
          userType: 'ADMIN',
        },
      } as unknown as Request;

      const res = {} as Response;
      const next = vi.fn() as NextFunction;

      const middleware = authorize(['CUSTOMER']); // Even if only CUSTOMER is allowed
      middleware(req, res, next);

      // Admin should always have access
      expect(next).toHaveBeenCalledWith();
    });

    it('should handle multiple allowed roles', async () => {
      const { user: agentUser } = await createUser({ userType: 'AGENT' });
      const { user: adminUser } = await createUser({ userType: 'ADMIN' });

      const middleware = authorize(['AGENT', 'ADMIN']);

      // Test agent
      const agentReq = {
        user: {
          userId: agentUser.id,
          userType: 'AGENT',
        },
      } as unknown as Request;

      const res = {} as Response;
      const nextAgent = vi.fn() as NextFunction;

      middleware(agentReq, res, nextAgent);
      expect(nextAgent).toHaveBeenCalledWith();

      // Test admin
      const adminReq = {
        user: {
          userId: adminUser.id,
          userType: 'ADMIN',
        },
      } as unknown as Request;

      const nextAdmin = vi.fn() as NextFunction;

      middleware(adminReq, res, nextAdmin);
      expect(nextAdmin).toHaveBeenCalledWith();
    });
  });
});
