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

    res.status(201).json({
      status: 'success',
      data: result,
    });
  }

  async login(req: Request, res: Response) {
    const data = loginSchema.parse(req.body);
    const result = await authService.login(data);

    res.json({
      status: 'success',
      data: result,
    });
  }

  async getMe(req: Request, res: Response) {
    const user = await authService.getMe(req.user!.userId);

    res.json({
      status: 'success',
      data: { user },
    });
  }

  async logout(req: Request, res: Response) {
    const { refreshToken } = req.body;

    if (refreshToken) {
      await authService.logout(refreshToken);
    }

    res.json({
      status: 'success',
      message: 'Logged out successfully',
    });
  }
}

export const authController = new AuthController();
