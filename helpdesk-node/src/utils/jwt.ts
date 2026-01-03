import jwt from 'jsonwebtoken';
import { config } from '../config/index.js';
import crypto from 'crypto';

export interface JWTPayload {
  userId: string;
  email?: string;
  userType: string;
  jti?: string;
}

// Main token generation function (used by tests)
export const generateToken = (payload: JWTPayload, expiresIn?: string): string => {
  // Add unique JWT ID to ensure tokens are always unique
  const tokenPayload = {
    ...payload,
    jti: crypto.randomBytes(16).toString('hex'),
  };

  return jwt.sign(tokenPayload, config.jwt.secret, {
    expiresIn: expiresIn || config.jwt.expiresIn,
  });
};

// Alias for access token
export const generateAccessToken = (payload: JWTPayload): string => {
  return generateToken(payload, config.jwt.expiresIn);
};

// Refresh token with longer expiry
export const generateRefreshToken = (payload: JWTPayload): string => {
  return generateToken(payload, config.jwt.refreshExpiresIn);
};

export const verifyToken = (token: string): JWTPayload => {
  return jwt.verify(token, config.jwt.secret) as JWTPayload;
};
