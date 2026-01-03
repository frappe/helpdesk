import { Request, Response, NextFunction } from 'express';
import { UnauthorizedError, ForbiddenError } from '../utils/errors.js';
import { verifyToken } from '../utils/jwt.js';

// Extend Express Request type to include user
declare global {
  namespace Express {
    interface Request {
      user?: {
        userId: string;
        email: string;
        userType: string;
      };
    }
  }
}

export const authenticate = (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      status: 'error',
      message: 'No token provided',
    });
  }

  const token = authHeader.substring(7);

  try {
    const payload = verifyToken(token);
    req.user = payload;
    next();
  } catch (error) {
    return res.status(401).json({
      status: 'error',
      message: 'Invalid token',
    });
  }
};

export const requireRole = (...roles: string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(403).json({
        status: 'error',
        message: 'Authentication required',
      });
    }

    // ADMIN users can access all endpoints
    if (req.user.userType === 'ADMIN') {
      return next();
    }

    if (!roles.includes(req.user.userType)) {
      return res.status(403).json({
        status: 'error',
        message: 'Insufficient permissions',
      });
    }

    next();
  };
};

// Authorize function that accepts an array of roles
export const authorize = (roles: string[]) => {
  return requireRole(...roles);
};

export const requireAgent = requireRole('AGENT', 'ADMIN');
export const requireAdmin = requireRole('ADMIN');
