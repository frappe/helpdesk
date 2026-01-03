import { Router } from 'express';
import { dashboardController } from '../controllers/dashboardController.js';
import { authenticate } from '../middleware/auth.js';

const router = Router();

router.get('/metrics', authenticate, (req, res) =>
  dashboardController.getMetrics(req, res)
);

export default router;
