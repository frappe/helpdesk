import { Request, Response } from 'express';
import { authService } from '../services/authService.js';
import { z } from 'zod';

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  fullName: z.string().min(2),
  userType: z.enum(['AGENT', 'CUSTOMER']).optional(),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

export class AuthController {
  async register(req: Request, res: Response) {
    const data = registerSchema.parse(req.body);
    const result = await authService.register(data);

    res.status(201).json(result);
  }

  async login(req: Request, res: Response) {
    const data = loginSchema.parse(req.body);
    const result = await authService.login(data);

    res.json(result);
  }

  async getMe(req: Request, res: Response) {
    const user = await authService.getMe(req.user!.userId);

    res.json(user);
  }

  async logout(req: Request, res: Response) {
    const { refreshToken } = req.body;

    if (refreshToken) {
      await authService.logout(refreshToken);
    } else {
      // If no specific token provided, logout all sessions for this user
      await authService.logoutAll(req.user!.userId);
    }

    res.json({
      message: 'Logged out successfully',
    });
  }

  async refreshToken(req: Request, res: Response) {
    const { refreshToken } = req.body;
    const result = await authService.refreshToken(refreshToken);

    res.json(result);
  }
}

export const authController = new AuthController();
