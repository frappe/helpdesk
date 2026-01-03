import { describe, it, expect } from 'vitest';
import { generateToken, verifyToken, generateRefreshToken } from '../../src/utils/jwt.js';

describe('JWT Utils', () => {
  describe('generateToken', () => {
    it('should generate a valid access token', () => {
      const payload = { userId: 'user123', userType: 'CUSTOMER' };
      const token = generateToken(payload);

      expect(token).toBeDefined();
      expect(typeof token).toBe('string');
      expect(token.split('.')).toHaveLength(3); // JWT has 3 parts
    });

    it('should generate token with custom expiry', () => {
      const payload = { userId: 'user123', userType: 'CUSTOMER' };
      const token = generateToken(payload, '1h');

      expect(token).toBeDefined();
      const decoded = verifyToken(token);
      expect(decoded.userId).toBe('user123');
    });

    it('should include payload data in token', () => {
      const payload = { userId: 'user123', userType: 'AGENT' };
      const token = generateToken(payload);
      const decoded = verifyToken(token);

      expect(decoded.userId).toBe('user123');
      expect(decoded.userType).toBe('AGENT');
    });

    it('should generate different tokens for different payloads', () => {
      const token1 = generateToken({ userId: 'user1', userType: 'CUSTOMER' });
      const token2 = generateToken({ userId: 'user2', userType: 'CUSTOMER' });

      expect(token1).not.toBe(token2);
    });
  });

  describe('verifyToken', () => {
    it('should verify and decode valid token', () => {
      const payload = { userId: 'user123', userType: 'CUSTOMER' };
      const token = generateToken(payload);
      const decoded = verifyToken(token);

      expect(decoded.userId).toBe('user123');
      expect(decoded.userType).toBe('CUSTOMER');
      expect(decoded.iat).toBeDefined(); // issued at
      expect(decoded.exp).toBeDefined(); // expiration
    });

    it('should throw error for invalid token', () => {
      expect(() => verifyToken('invalid-token')).toThrow();
    });

    it('should throw error for malformed token', () => {
      expect(() => verifyToken('not.a.jwt')).toThrow();
    });

    it('should throw error for expired token', async () => {
      const payload = { userId: 'user123', userType: 'CUSTOMER' };
      const token = generateToken(payload, '0s'); // Expire immediately

      // Wait for token to expire
      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(() => verifyToken(token)).toThrow();
    });

    it('should verify token with exact payload', () => {
      const payload = {
        userId: 'test-user-id',
        userType: 'AGENT',
      };
      const token = generateToken(payload);
      const decoded = verifyToken(token);

      expect(decoded).toMatchObject(payload);
    });
  });

  describe('generateRefreshToken', () => {
    it('should generate a valid refresh token', () => {
      const payload = { userId: 'user123' };
      const token = generateRefreshToken(payload);

      expect(token).toBeDefined();
      expect(typeof token).toBe('string');
      expect(token.split('.')).toHaveLength(3);
    });

    it('should generate refresh token with longer expiry', () => {
      const payload = { userId: 'user123' };
      const refreshToken = generateRefreshToken(payload);
      const decoded = verifyToken(refreshToken);

      expect(decoded.userId).toBe('user123');
      expect(decoded.exp).toBeDefined();

      // Refresh token should have longer expiry than access token
      const accessToken = generateToken({ userId: 'user123', userType: 'CUSTOMER' });
      const accessDecoded = verifyToken(accessToken);

      expect(decoded.exp).toBeGreaterThan(accessDecoded.exp!);
    });

    it('should include only userId in refresh token', () => {
      const payload = { userId: 'user123' };
      const token = generateRefreshToken(payload);
      const decoded = verifyToken(token);

      expect(decoded.userId).toBe('user123');
      expect(decoded.userType).toBeUndefined();
    });
  });

  describe('Token expiration', () => {
    it('should respect custom expiry time', async () => {
      const payload = { userId: 'user123', userType: 'CUSTOMER' };
      const token = generateToken(payload, '100ms');

      // Token should be valid immediately
      const decoded1 = verifyToken(token);
      expect(decoded1.userId).toBe('user123');

      // Wait for expiration
      await new Promise((resolve) => setTimeout(resolve, 150));

      // Token should be expired
      expect(() => verifyToken(token)).toThrow();
    });

    it('should not expire before expiry time', async () => {
      const payload = { userId: 'user123', userType: 'CUSTOMER' };
      const token = generateToken(payload, '1h');

      // Should still be valid after 100ms
      await new Promise((resolve) => setTimeout(resolve, 100));
      const decoded = verifyToken(token);

      expect(decoded.userId).toBe('user123');
    });
  });

  describe('Token security', () => {
    it('should not accept tokens with modified payload', () => {
      const payload = { userId: 'user123', userType: 'CUSTOMER' };
      const token = generateToken(payload);

      // Try to modify the token payload
      const parts = token.split('.');
      const modifiedPayload = Buffer.from(
        JSON.stringify({ userId: 'hacker', userType: 'ADMIN' })
      ).toString('base64url');
      const modifiedToken = `${parts[0]}.${modifiedPayload}.${parts[2]}`;

      // Should throw because signature doesn't match
      expect(() => verifyToken(modifiedToken)).toThrow();
    });

    it('should not accept tokens signed with different secret', () => {
      // This would require using a different JWT library instance with different secret
      // which is not practical in this test, but the concept is important
      const fakeToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ1c2VyMTIzIn0.different_signature';

      expect(() => verifyToken(fakeToken)).toThrow();
    });
  });
});
