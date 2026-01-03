import { prisma } from '../utils/prisma.js';
import { NotFoundError, ForbiddenError } from '../utils/errors.js';
import { Prisma } from '@prisma/client';
import {
  emitTicketCreated,
  emitTicketUpdated,
  emitTicketAssigned,
  emitCommentAdded,
} from '../utils/socket.js';

interface CreateTicketData {
  subject: string;
  description?: string;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  ticketType?: string;
  customerId?: string;
  raisedById: string;
}

interface UpdateTicketData {
  subject?: string;
  description?: string;
  status?: string;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  assignedToId?: string;
  teamId?: string;
  resolution?: string;
}

interface ListTicketsQuery {
  page?: number;
  limit?: number;
  status?: string;
  priority?: string;
  assignedToId?: string;
  customerId?: string;
  search?: string;
}

export class TicketService {
  async createTicket(data: CreateTicketData) {
    // Auto-assign customer if not provided
    let customerId = data.customerId;
    if (!customerId) {
      const customer = await prisma.customer.findUnique({
        where: { userId: data.raisedById },
      });
      customerId = customer?.id;
    }

    if (!customerId) {
      throw new NotFoundError('Customer not found');
    }

    const ticket = await prisma.ticket.create({
      data: {
        subject: data.subject,
        description: data.description,
        priority: data.priority || 'MEDIUM',
        ticketType: data.ticketType,
        customerId,
        raisedById: data.raisedById,
        status: 'Open',
      },
      include: {
        customer: {
          include: { user: true },
        },
        raisedBy: true,
        assignedTo: true,
      },
    });

    // Log activity
    await this.logActivity(ticket.id, data.raisedById, 'created', null, null, null);

    // Emit real-time event
    emitTicketCreated(ticket);

    return ticket;
  }

  async listTickets(query: ListTicketsQuery, userId: string, userType: string) {
    const page = query.page || 1;
    const limit = query.limit || 20;
    const skip = (page - 1) * limit;

    const where: Prisma.TicketWhereInput = {};

    // Apply filters
    if (query.status) where.status = query.status;
    if (query.priority) where.priority = query.priority as any;
    if (query.assignedToId) where.assignedToId = query.assignedToId;

    // Role-based filtering
    if (userType === 'CUSTOMER') {
      const customer = await prisma.customer.findUnique({
        where: { userId },
      });
      where.customerId = customer?.id;
    } else if (query.customerId) {
      where.customerId = query.customerId;
    }

    // Search
    if (query.search) {
      where.OR = [
        { subject: { contains: query.search, mode: 'insensitive' } },
        { description: { contains: query.search, mode: 'insensitive' } },
      ];
    }

    const [tickets, total] = await Promise.all([
      prisma.ticket.findMany({
        where,
        include: {
          customer: {
            include: { user: true },
          },
          raisedBy: true,
          assignedTo: true,
          team: true,
          _count: {
            select: { comments: true },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      prisma.ticket.count({ where }),
    ]);

    return {
      data: tickets,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async getTicket(id: string, userId: string, userType: string) {
    const ticket = await prisma.ticket.findUnique({
      where: { id },
      include: {
        customer: {
          include: { user: true },
        },
        raisedBy: true,
        assignedTo: true,
        team: true,
        comments: {
          include: {
            user: true,
            attachments: true,
          },
          orderBy: { createdAt: 'desc' },
        },
        activities: {
          include: {
            user: true,
          },
          orderBy: { createdAt: 'desc' },
          take: 50,
        },
        attachments: true,
      },
    });

    if (!ticket) {
      throw new NotFoundError('Ticket not found');
    }

    // Check permissions
    if (userType === 'CUSTOMER') {
      const customer = await prisma.customer.findUnique({
        where: { userId },
      });
      if (ticket.customerId !== customer?.id) {
        throw new ForbiddenError('Access denied');
      }
    }

    return ticket;
  }

  async updateTicket(
    id: string,
    data: UpdateTicketData,
    userId: string,
    userType: string
  ) {
    const existingTicket = await prisma.ticket.findUnique({
      where: { id },
    });

    if (!existingTicket) {
      throw new NotFoundError('Ticket not found');
    }

    // Check permissions
    if (userType === 'CUSTOMER') {
      const customer = await prisma.customer.findUnique({
        where: { userId },
      });
      if (existingTicket.customerId !== customer?.id) {
        throw new ForbiddenError('Access denied');
      }
      // Customers can only update certain fields
      delete data.status;
      delete data.assignedToId;
      delete data.teamId;
    }

    const ticket = await prisma.ticket.update({
      where: { id },
      data,
      include: {
        customer: {
          include: { user: true },
        },
        raisedBy: true,
        assignedTo: true,
        team: true,
      },
    });

    // Log activities for changed fields
    const changes = Object.keys(data) as (keyof UpdateTicketData)[];
    for (const field of changes) {
      if (data[field] !== undefined && data[field] !== existingTicket[field as keyof typeof existingTicket]) {
        await this.logActivity(
          id,
          userId,
          'updated',
          String(field),
          String(existingTicket[field as keyof typeof existingTicket] || ''),
          String(data[field])
        );
      }
    }

    // Emit real-time event
    emitTicketUpdated(id, ticket);

    return ticket;
  }

  async deleteTicket(id: string, userId: string, userType: string) {
    const ticket = await prisma.ticket.findUnique({
      where: { id },
    });

    if (!ticket) {
      throw new NotFoundError('Ticket not found');
    }

    // Only admins can delete tickets
    if (userType !== 'ADMIN') {
      throw new ForbiddenError('Only admins can delete tickets');
    }

    await prisma.ticket.delete({
      where: { id },
    });

    return { message: 'Ticket deleted successfully' };
  }

  async addComment(ticketId: string, userId: string, content: string, isInternal = false, userType?: string) {
    // Verify ticket exists
    const ticket = await prisma.ticket.findUnique({
      where: { id: ticketId },
    });

    if (!ticket) {
      throw new NotFoundError('Ticket not found');
    }

    // Customers cannot create internal comments
    if (userType === 'CUSTOMER') {
      isInternal = false;
    }

    const comment = await prisma.comment.create({
      data: {
        ticketId,
        userId,
        content,
        isInternal,
      },
      include: {
        user: true,
        attachments: true,
      },
    });

    // Log activity
    await this.logActivity(ticketId, userId, 'commented', null, null, null);

    // Emit real-time event
    emitCommentAdded(ticketId, comment);

    return comment;
  }

  async assignTicket(ticketId: string, assignedToId: string, userId: string) {
    const ticket = await prisma.ticket.update({
      where: { id: ticketId },
      data: { assignedToId },
      include: {
        assignedTo: true,
      },
    });

    // Log activity
    await this.logActivity(
      ticketId,
      userId,
      'updated',
      'assignedToId',
      '',
      assignedToId
    );

    // Emit real-time event
    emitTicketAssigned(ticketId, assignedToId, ticket);

    return ticket;
  }

  private async logActivity(
    ticketId: string,
    userId: string,
    action: string,
    fieldName: string | null,
    oldValue: string | null,
    newValue: string | null
  ) {
    await prisma.activity.create({
      data: {
        ticketId,
        userId,
        action,
        fieldName,
        oldValue,
        newValue,
      },
    });
  }
}

export const ticketService = new TicketService();
