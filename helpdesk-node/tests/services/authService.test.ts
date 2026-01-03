import { describe, it, expect, beforeEach } from 'vitest';
import { AuthService } from '../../src/services/authService.js';
import { createUser, createCustomer } from '../factories/userFactory.js';
import { ConflictError, UnauthorizedError } from '../../src/utils/errors.js';
import { prisma } from '../setup.js';

describe('AuthService', () => {
  let authService: AuthService;

  beforeEach(() => {
    authService = new AuthService();
  });

  describe('register', () => {
    it('should register a new user successfully', async () => {
      const result = await authService.register({
        email: 'newuser@example.com',
        password: 'password123',
        fullName: 'New User',
        userType: 'CUSTOMER',
      });

      expect(result.user).toBeDefined();
      expect(result.user.email).toBe('newuser@example.com');
      expect(result.user.fullName).toBe('New User');
      expect(result.user.userType).toBe('CUSTOMER');
      expect(result.accessToken).toBeDefined();
      expect(result.refreshToken).toBeDefined();
    });

    it('should create customer profile for customer user type', async () => {
      const result = await authService.register({
        email: 'customer@example.com',
        password: 'password123',
        fullName: 'Test Customer',
        userType: 'CUSTOMER',
      });

      const customer = await prisma.customer.findUnique({
        where: { userId: result.user.id },
      });

      expect(customer).toBeDefined();
      expect(customer?.customerName).toBe('Test Customer');
    });

    it('should create agent profile for agent user type', async () => {
      const result = await authService.register({
        email: 'agent@example.com',
        password: 'password123',
        fullName: 'Test Agent',
        userType: 'AGENT',
      });

      const agent = await prisma.agent.findUnique({
        where: { userId: result.user.id },
      });

      expect(agent).toBeDefined();
      expect(agent?.agentName).toBe('Test Agent');
    });

    it('should throw ConflictError for duplicate email', async () => {
      await createUser({ email: 'duplicate@example.com' });

      await expect(
        authService.register({
          email: 'duplicate@example.com',
          password: 'password123',
          fullName: 'Duplicate User',
        })
      ).rejects.toThrow(ConflictError);
    });

    it('should hash password before storing', async () => {
      const password = 'mySecretPassword';
      const result = await authService.register({
        email: 'hashtest@example.com',
        password,
        fullName: 'Hash Test',
      });

      const user = await prisma.user.findUnique({
        where: { id: result.user.id },
      });

      expect(user?.password).not.toBe(password);
      expect(user?.password.length).toBeGreaterThan(20); // Bcrypt hash length
    });
  });

  describe('login', () => {
    it('should login successfully with correct credentials', async () => {
      const email = 'login@example.com';
      const password = 'password123';
      await createUser({ email, password });

      const result = await authService.login({ email, password });

      expect(result.user).toBeDefined();
      expect(result.user.email).toBe(email);
      expect(result.accessToken).toBeDefined();
      expect(result.refreshToken).toBeDefined();
    });

    it('should throw UnauthorizedError for non-existent user', async () => {
      await expect(
        authService.login({
          email: 'nonexistent@example.com',
          password: 'password123',
        })
      ).rejects.toThrow(UnauthorizedError);
    });

    it('should throw UnauthorizedError for incorrect password', async () => {
      const email = 'wrongpass@example.com';
      await createUser({ email, password: 'correctPassword' });

      await expect(
        authService.login({
          email,
          password: 'wrongPassword',
        })
      ).rejects.toThrow(UnauthorizedError);
    });

    it('should throw UnauthorizedError for inactive user', async () => {
      const email = 'inactive@example.com';
      const { user } = await createUser({ email });

      // Deactivate user
      await prisma.user.update({
        where: { id: user.id },
        data: { isActive: false },
      });

      await expect(
        authService.login({
          email,
          password: 'password123',
        })
      ).rejects.toThrow(UnauthorizedError);
    });

    it('should create refresh token on login', async () => {
      const email = 'refresh@example.com';
      const password = 'password123';
      const { user } = await createUser({ email, password });

      const result = await authService.login({ email, password });

      const refreshToken = await prisma.refreshToken.findFirst({
        where: { userId: user.id },
      });

      expect(refreshToken).toBeDefined();
      expect(refreshToken?.token).toBe(result.refreshToken);
    });
  });

  describe('getMe', () => {
    it('should return user with customer profile', async () => {
      const { user, customer } = await createCustomer();

      const result = await authService.getMe(user.id);

      expect(result).toBeDefined();
      expect(result.id).toBe(user.id);
      expect(result.customer).toBeDefined();
      expect(result.customer?.id).toBe(customer.id);
    });

    it('should throw UnauthorizedError for non-existent user', async () => {
      await expect(authService.getMe('non-existent-id')).rejects.toThrow(
        UnauthorizedError
      );
    });
  });

  describe('logout', () => {
    it('should delete refresh token on logout', async () => {
      const email = 'logout@example.com';
      const password = 'password123';
      await createUser({ email, password });

      const loginResult = await authService.login({ email, password });

      await authService.logout(loginResult.refreshToken);

      const refreshToken = await prisma.refreshToken.findUnique({
        where: { token: loginResult.refreshToken },
      });

      expect(refreshToken).toBeNull();
    });
  });
});
