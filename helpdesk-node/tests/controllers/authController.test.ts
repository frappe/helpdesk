import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import express from 'express';
import authRoutes from '../../src/routes/auth.routes.js';
import { errorHandler } from '../../src/middleware/errorHandler.js';
import { prisma } from '../setup.js';
import { createUser } from '../factories/userFactory.js';
import bcrypt from 'bcryptjs';

// Create a test Express app
const app = express();
app.use(express.json());
app.use('/auth', authRoutes);
app.use(errorHandler);

describe('AuthController', () => {
  describe('POST /auth/register', () => {
    it('should register a new user successfully', async () => {
      const response = await request(app)
        .post('/auth/register')
        .send({
          email: 'newuser@example.com',
          password: 'Password123!',
          fullName: 'New User',
          userType: 'CUSTOMER',
        });

      expect(response.status).toBe(201);
      expect(response.body.user).toBeDefined();
      expect(response.body.user.email).toBe('newuser@example.com');
      expect(response.body.user.fullName).toBe('New User');
      expect(response.body.accessToken).toBeDefined();
      expect(response.body.refreshToken).toBeDefined();
      expect(response.body.user.password).toBeUndefined(); // Password should not be in response
    });

    it('should return 400 for missing required fields', async () => {
      const response = await request(app)
        .post('/auth/register')
        .send({
          email: 'incomplete@example.com',
          // Missing password, fullName, userType
        });

      expect(response.status).toBe(400);
    });

    it('should return 400 for invalid email format', async () => {
      const response = await request(app)
        .post('/auth/register')
        .send({
          email: 'invalid-email',
          password: 'Password123!',
          fullName: 'Test User',
          userType: 'CUSTOMER',
        });

      expect(response.status).toBe(400);
    });

    it('should return 409 for duplicate email', async () => {
      const email = 'duplicate@example.com';
      await createUser({ email });

      const response = await request(app)
        .post('/auth/register')
        .send({
          email,
          password: 'Password123!',
          fullName: 'Duplicate User',
          userType: 'CUSTOMER',
        });

      expect(response.status).toBe(409);
      expect(response.body.message).toContain('already exists');
    });

    it('should create customer profile for CUSTOMER userType', async () => {
      const response = await request(app)
        .post('/auth/register')
        .send({
          email: 'customer@example.com',
          password: 'Password123!',
          fullName: 'Customer User',
          userType: 'CUSTOMER',
        });

      expect(response.status).toBe(201);

      const customer = await prisma.customer.findFirst({
        where: { userId: response.body.user.id },
      });
      expect(customer).toBeDefined();
      expect(customer?.customerName).toBe('Customer User');
    });
  });

  describe('POST /auth/login', () => {
    it('should login successfully with valid credentials', async () => {
      const password = 'Password123!';
      const { user } = await createUser({ password });

      const response = await request(app)
        .post('/auth/login')
        .send({
          email: user.email,
          password,
        });

      expect(response.status).toBe(200);
      expect(response.body.user).toBeDefined();
      expect(response.body.user.email).toBe(user.email);
      expect(response.body.accessToken).toBeDefined();
      expect(response.body.refreshToken).toBeDefined();
    });

    it('should return 401 for invalid email', async () => {
      const response = await request(app)
        .post('/auth/login')
        .send({
          email: 'nonexistent@example.com',
          password: 'Password123!',
        });

      expect(response.status).toBe(401);
      expect(response.body.message).toContain('Invalid credentials');
    });

    it('should return 401 for invalid password', async () => {
      const { user } = await createUser({ password: 'CorrectPassword' });

      const response = await request(app)
        .post('/auth/login')
        .send({
          email: user.email,
          password: 'WrongPassword',
        });

      expect(response.status).toBe(401);
      expect(response.body.message).toContain('Invalid credentials');
    });

    it('should return 401 for inactive user', async () => {
      const password = 'Password123!';
      const { user } = await createUser({ password, isActive: false });

      const response = await request(app)
        .post('/auth/login')
        .send({
          email: user.email,
          password,
        });

      expect(response.status).toBe(401);
      expect(response.body.message).toContain('inactive');
    });

    it('should create refresh token on login', async () => {
      const password = 'Password123!';
      const { user } = await createUser({ password });

      const response = await request(app)
        .post('/auth/login')
        .send({
          email: user.email,
          password,
        });

      expect(response.status).toBe(200);

      const refreshToken = await prisma.refreshToken.findFirst({
        where: { userId: user.id },
      });
      expect(refreshToken).toBeDefined();
    });
  });

  describe('GET /auth/me', () => {
    it('should return user profile with valid token', async () => {
      const password = 'Password123!';
      const { user } = await createUser({ password });

      // Login to get token
      const loginResponse = await request(app)
        .post('/auth/login')
        .send({ email: user.email, password });

      const token = loginResponse.body.accessToken;

      // Get profile
      const response = await request(app)
        .get('/auth/me')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.id).toBe(user.id);
      expect(response.body.email).toBe(user.email);
      expect(response.body.password).toBeUndefined();
    });

    it('should return 401 without token', async () => {
      const response = await request(app).get('/auth/me');

      expect(response.status).toBe(401);
    });

    it('should return 401 with invalid token', async () => {
      const response = await request(app)
        .get('/auth/me')
        .set('Authorization', 'Bearer invalid-token');

      expect(response.status).toBe(401);
    });
  });

  describe('POST /auth/logout', () => {
    it('should logout successfully', async () => {
      const password = 'Password123!';
      const { user } = await createUser({ password });

      // Login first
      const loginResponse = await request(app)
        .post('/auth/login')
        .send({ email: user.email, password });

      const token = loginResponse.body.accessToken;

      // Logout
      const response = await request(app)
        .post('/auth/logout')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.message).toContain('success');

      // Verify refresh token was deleted
      const refreshTokens = await prisma.refreshToken.findMany({
        where: { userId: user.id },
      });
      expect(refreshTokens.length).toBe(0);
    });

    it('should return 401 without token', async () => {
      const response = await request(app).post('/auth/logout');

      expect(response.status).toBe(401);
    });
  });

  describe('POST /auth/refresh', () => {
    it('should refresh token successfully', async () => {
      const password = 'Password123!';
      const { user } = await createUser({ password });

      // Login to get refresh token
      const loginResponse = await request(app)
        .post('/auth/login')
        .send({ email: user.email, password });

      const refreshToken = loginResponse.body.refreshToken;

      // Refresh
      const response = await request(app)
        .post('/auth/refresh')
        .send({ refreshToken });

      expect(response.status).toBe(200);
      expect(response.body.accessToken).toBeDefined();
      expect(response.body.refreshToken).toBeDefined();
      expect(response.body.accessToken).not.toBe(loginResponse.body.accessToken);
    });

    it('should return 401 for invalid refresh token', async () => {
      const response = await request(app)
        .post('/auth/refresh')
        .send({ refreshToken: 'invalid-token' });

      expect(response.status).toBe(401);
    });

    it('should return 401 for expired refresh token', async () => {
      const password = 'Password123!';
      const { user } = await createUser({ password });

      // Create expired refresh token
      const expiredToken = await prisma.refreshToken.create({
        data: {
          token: 'expired-token',
          userId: user.id,
          expiresAt: new Date(Date.now() - 1000), // Expired 1 second ago
        },
      });

      const response = await request(app)
        .post('/auth/refresh')
        .send({ refreshToken: expiredToken.token });

      expect(response.status).toBe(401);
    });
  });
});
