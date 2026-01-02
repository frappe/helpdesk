import { Router } from 'express';
import authRoutes from './auth.routes.js';
import ticketRoutes from './ticket.routes.js';
import dashboardRoutes from './dashboard.routes.js';
import kbRoutes from './kb.routes.js';
import uploadRoutes from './upload.routes.js';
import searchRoutes from './search.routes.js';

const router = Router();

router.use('/auth', authRoutes);
router.use('/tickets', ticketRoutes);
router.use('/dashboard', dashboardRoutes);
router.use('/kb', kbRoutes);
router.use('/upload', uploadRoutes);
router.use('/search', searchRoutes);

export default router;
