import { describe, it, expect } from 'vitest';
import {
  AppError,
  BadRequestError,
  UnauthorizedError,
  ForbiddenError,
  NotFoundError,
  ConflictError,
  ValidationError,
} from '../../src/utils/errors.js';

describe('Custom Error Classes', () => {
  describe('AppError', () => {
    it('should create error with message and status code', () => {
      const error = new AppError('Test error', 500);

      expect(error.message).toBe('Test error');
      expect(error.statusCode).toBe(500);
      expect(error instanceof Error).toBe(true);
    });

    it('should have default status code 500', () => {
      const error = new AppError('Test error');

      expect(error.statusCode).toBe(500);
    });

    it('should maintain error name', () => {
      const error = new AppError('Test error');

      expect(error.name).toBe('AppError');
    });

    it('should be catchable as Error', () => {
      try {
        throw new AppError('Test error');
      } catch (error) {
        expect(error instanceof Error).toBe(true);
        expect(error instanceof AppError).toBe(true);
      }
    });
  });

  describe('BadRequestError', () => {
    it('should create 400 error', () => {
      const error = new BadRequestError('Invalid input');

      expect(error.message).toBe('Invalid input');
      expect(error.statusCode).toBe(400);
      expect(error.name).toBe('BadRequestError');
    });

    it('should extend AppError', () => {
      const error = new BadRequestError('Invalid input');

      expect(error instanceof AppError).toBe(true);
      expect(error instanceof Error).toBe(true);
    });

    it('should have default message', () => {
      const error = new BadRequestError();

      expect(error.message).toBe('Bad request');
      expect(error.statusCode).toBe(400);
    });
  });

  describe('UnauthorizedError', () => {
    it('should create 401 error', () => {
      const error = new UnauthorizedError('Invalid token');

      expect(error.message).toBe('Invalid token');
      expect(error.statusCode).toBe(401);
      expect(error.name).toBe('UnauthorizedError');
    });

    it('should extend AppError', () => {
      const error = new UnauthorizedError('Invalid token');

      expect(error instanceof AppError).toBe(true);
    });

    it('should have default message', () => {
      const error = new UnauthorizedError();

      expect(error.message).toBe('Unauthorized');
      expect(error.statusCode).toBe(401);
    });
  });

  describe('ForbiddenError', () => {
    it('should create 403 error', () => {
      const error = new ForbiddenError('Insufficient permissions');

      expect(error.message).toBe('Insufficient permissions');
      expect(error.statusCode).toBe(403);
      expect(error.name).toBe('ForbiddenError');
    });

    it('should extend AppError', () => {
      const error = new ForbiddenError('Insufficient permissions');

      expect(error instanceof AppError).toBe(true);
    });

    it('should have default message', () => {
      const error = new ForbiddenError();

      expect(error.message).toBe('Forbidden');
      expect(error.statusCode).toBe(403);
    });
  });

  describe('NotFoundError', () => {
    it('should create 404 error', () => {
      const error = new NotFoundError('Resource not found');

      expect(error.message).toBe('Resource not found');
      expect(error.statusCode).toBe(404);
      expect(error.name).toBe('NotFoundError');
    });

    it('should extend AppError', () => {
      const error = new NotFoundError('Resource not found');

      expect(error instanceof AppError).toBe(true);
    });

    it('should have default message', () => {
      const error = new NotFoundError();

      expect(error.message).toBe('Resource not found');
      expect(error.statusCode).toBe(404);
    });

    it('should support dynamic resource names', () => {
      const error = new NotFoundError('User not found');
      expect(error.message).toBe('User not found');

      const error2 = new NotFoundError('Ticket not found');
      expect(error2.message).toBe('Ticket not found');
    });
  });

  describe('ConflictError', () => {
    it('should create 409 error', () => {
      const error = new ConflictError('Email already exists');

      expect(error.message).toBe('Email already exists');
      expect(error.statusCode).toBe(409);
      expect(error.name).toBe('ConflictError');
    });

    it('should extend AppError', () => {
      const error = new ConflictError('Duplicate entry');

      expect(error instanceof AppError).toBe(true);
    });

    it('should have default message', () => {
      const error = new ConflictError();

      expect(error.message).toBe('Conflict');
      expect(error.statusCode).toBe(409);
    });
  });

  describe('ValidationError', () => {
    it('should create 422 error with validation errors', () => {
      const errors = [
        { field: 'email', message: 'Invalid email format' },
        { field: 'password', message: 'Password too short' },
      ];

      const error = new ValidationError('Validation failed', errors);

      expect(error.message).toBe('Validation failed');
      expect(error.statusCode).toBe(422);
      expect(error.name).toBe('ValidationError');
      expect(error.errors).toEqual(errors);
    });

    it('should extend AppError', () => {
      const error = new ValidationError('Validation failed');

      expect(error instanceof AppError).toBe(true);
    });

    it('should have default message', () => {
      const error = new ValidationError();

      expect(error.message).toBe('Validation error');
      expect(error.statusCode).toBe(422);
    });

    it('should handle empty errors array', () => {
      const error = new ValidationError('Validation failed', []);

      expect(error.errors).toEqual([]);
    });

    it('should handle single validation error', () => {
      const errors = [{ field: 'email', message: 'Email is required' }];
      const error = new ValidationError('Validation failed', errors);

      expect(error.errors).toHaveLength(1);
      expect(error.errors![0].field).toBe('email');
    });

    it('should handle multiple validation errors', () => {
      const errors = [
        { field: 'email', message: 'Invalid email' },
        { field: 'password', message: 'Too short' },
        { field: 'name', message: 'Required' },
      ];

      const error = new ValidationError('Validation failed', errors);

      expect(error.errors).toHaveLength(3);
      expect(error.errors).toEqual(errors);
    });
  });

  describe('Error inheritance chain', () => {
    it('should all inherit from AppError', () => {
      const errors = [
        new BadRequestError(),
        new UnauthorizedError(),
        new ForbiddenError(),
        new NotFoundError(),
        new ConflictError(),
        new ValidationError(),
      ];

      errors.forEach((error) => {
        expect(error instanceof AppError).toBe(true);
        expect(error instanceof Error).toBe(true);
      });
    });

    it('should maintain instanceof checks', () => {
      const badRequest = new BadRequestError();
      const notFound = new NotFoundError();

      expect(badRequest instanceof BadRequestError).toBe(true);
      expect(badRequest instanceof NotFoundError).toBe(false);

      expect(notFound instanceof NotFoundError).toBe(true);
      expect(notFound instanceof BadRequestError).toBe(false);
    });
  });

  describe('Error serialization', () => {
    it('should serialize to JSON', () => {
      const error = new BadRequestError('Invalid input');
      const json = JSON.parse(JSON.stringify(error));

      expect(json.message).toBe('Invalid input');
    });

    it('should preserve custom properties', () => {
      const errors = [{ field: 'email', message: 'Invalid' }];
      const error = new ValidationError('Validation failed', errors);

      const serialized = JSON.parse(JSON.stringify(error));
      expect(serialized.errors).toEqual(errors);
    });

    it('should include statusCode in serialization', () => {
      const error = new NotFoundError('User not found');

      expect(error.statusCode).toBe(404);
    });
  });

  describe('Error stack traces', () => {
    it('should include stack trace', () => {
      const error = new AppError('Test error');

      expect(error.stack).toBeDefined();
      expect(error.stack).toContain('AppError');
    });

    it('should maintain stack trace for all error types', () => {
      const errors = [
        new BadRequestError(),
        new UnauthorizedError(),
        new ForbiddenError(),
        new NotFoundError(),
        new ConflictError(),
        new ValidationError(),
      ];

      errors.forEach((error) => {
        expect(error.stack).toBeDefined();
      });
    });
  });

  describe('Error usage in throw statements', () => {
    it('should throw and catch BadRequestError', () => {
      expect(() => {
        throw new BadRequestError('Invalid data');
      }).toThrow(BadRequestError);
    });

    it('should throw and catch NotFoundError', () => {
      expect(() => {
        throw new NotFoundError('User not found');
      }).toThrow(NotFoundError);
    });

    it('should catch as AppError', () => {
      try {
        throw new UnauthorizedError('Invalid token');
      } catch (error) {
        expect(error instanceof AppError).toBe(true);
        if (error instanceof AppError) {
          expect(error.statusCode).toBe(401);
        }
      }
    });

    it('should differentiate error types in catch', () => {
      try {
        throw new ValidationError('Validation failed', [
          { field: 'email', message: 'Invalid' },
        ]);
      } catch (error) {
        if (error instanceof ValidationError) {
          expect(error.errors).toBeDefined();
          expect(error.errors).toHaveLength(1);
        } else {
          throw new Error('Wrong error type caught');
        }
      }
    });
  });
});
