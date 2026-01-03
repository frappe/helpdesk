import jwt from 'jsonwebtoken';
import { config } from '../config/index.js';

export interface JWTPayload {
  userId: string;
  email?: string;
  userType: string;
}

// Main token generation function (used by tests)
export const generateToken = (payload: JWTPayload, expiresIn?: string): string => {
  return jwt.sign(payload, config.jwt.secret, {
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
