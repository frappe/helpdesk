import { Router } from 'express';
import { searchController } from '../controllers/searchController.js';
import { authenticate, requireAgent } from '../middleware/auth.js';

const router = Router();

// All search routes require authentication
router.use(authenticate);

// Global search (searches across all entities)
router.get('/', (req, res) => searchController.globalSearch(req, res));

// Entity-specific searches
router.get('/tickets', (req, res) => searchController.searchTickets(req, res));
router.get('/articles', (req, res) => searchController.searchArticles(req, res));
router.get('/customers', requireAgent, (req, res) => searchController.searchCustomers(req, res));

export default router;
