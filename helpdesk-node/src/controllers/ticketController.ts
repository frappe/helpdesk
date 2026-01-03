import { Request, Response } from 'express';
import { ticketService } from '../services/ticketService.js';
import { z } from 'zod';

const createTicketSchema = z.object({
  subject: z.string().min(5),
  description: z.string().optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  ticketType: z.string().optional(),
  customerId: z.string().optional(),
});

const updateTicketSchema = z.object({
  subject: z.string().min(5).optional(),
  description: z.string().optional(),
  status: z.string().optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  assignedToId: z.string().optional(),
  teamId: z.string().optional(),
  resolution: z.string().optional(),
});

const addCommentSchema = z.object({
  content: z.string().min(1),
  isInternal: z.boolean().optional(),
});

const assignTicketSchema = z.object({
  assignedToId: z.string(),
});

export class TicketController {
  async createTicket(req: Request, res: Response) {
    const data = createTicketSchema.parse(req.body);
    const ticket = await ticketService.createTicket({
      ...data,
      raisedById: req.user!.userId,
    });

    res.status(201).json(ticket);
  }

  async listTickets(req: Request, res: Response) {
    const result = await ticketService.listTickets(
      {
        page: req.query.page ? parseInt(req.query.page as string) : undefined,
        limit: req.query.limit ? parseInt(req.query.limit as string) : undefined,
        status: req.query.status as string,
        priority: req.query.priority as string,
        assignedToId: req.query.assignedToId as string,
        customerId: req.query.customerId as string,
        search: req.query.search as string,
      },
      req.user!.userId,
      req.user!.userType
    );

    res.json(result);
  }

  async getTicket(req: Request, res: Response) {
    const { id } = req.params;
    const ticket = await ticketService.getTicket(
      id,
      req.user!.userId,
      req.user!.userType
    );

    res.json(ticket);
  }

  async updateTicket(req: Request, res: Response) {
    const { id } = req.params;
    const data = updateTicketSchema.parse(req.body);
    const ticket = await ticketService.updateTicket(
      id,
      data,
      req.user!.userId,
      req.user!.userType
    );

    res.json(ticket);
  }

  async deleteTicket(req: Request, res: Response) {
    const { id } = req.params;
    await ticketService.deleteTicket(
      id,
      req.user!.userId,
      req.user!.userType
    );

    res.status(204).send();
  }

  async addComment(req: Request, res: Response) {
    const { id } = req.params;
    const data = addCommentSchema.parse(req.body);
    const comment = await ticketService.addComment(
      id,
      req.user!.userId,
      data.content,
      data.isInternal,
      req.user!.userType
    );

    res.status(201).json(comment);
  }

  async assignTicket(req: Request, res: Response) {
    const { id } = req.params;
    const data = assignTicketSchema.parse(req.body);
    const ticket = await ticketService.assignTicket(
      id,
      data.assignedToId,
      req.user!.userId
    );

    res.json(ticket);
  }
}

export const ticketController = new TicketController();
