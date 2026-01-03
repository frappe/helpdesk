import { Router } from 'express';
import { ticketController } from '../controllers/ticketController.js';
import { authenticate } from '../middleware/auth.js';

const router = Router();

// All ticket routes require authentication
router.use(authenticate);

router.post('/', (req, res) => ticketController.createTicket(req, res));
router.get('/', (req, res) => ticketController.listTickets(req, res));
router.get('/:id', (req, res) => ticketController.getTicket(req, res));
router.patch('/:id', (req, res) => ticketController.updateTicket(req, res));
router.delete('/:id', (req, res) => ticketController.deleteTicket(req, res));

// Comments
router.post('/:id/comments', (req, res) => ticketController.addComment(req, res));

// Assignment
router.patch('/:id/assign', (req, res) => ticketController.assignTicket(req, res));

export default router;
