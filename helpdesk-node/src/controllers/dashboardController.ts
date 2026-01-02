import { Request, Response } from 'express';
import { dashboardService } from '../services/dashboardService.js';

export class DashboardController {
  async getMetrics(req: Request, res: Response) {
    const metrics = await dashboardService.getDashboardMetrics(
      req.user!.userId,
      req.user!.userType
    );

    res.json({
      status: 'success',
      data: metrics,
    });
  }
}

export const dashboardController = new DashboardController();
