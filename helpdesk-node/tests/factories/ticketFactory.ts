import { prisma } from '../setup.js';
import { createCustomer, createAgent } from './userFactory.js';
import { TicketPriority } from '@prisma/client';

export const createTicket = async (overrides?: {
  subject?: string;
  description?: string;
  status?: string;
  priority?: TicketPriority;
  customerId?: string;
  raisedById?: string;
  assignedToId?: string;
}) => {
  // Create customer and agent if not provided
  let customerId = overrides?.customerId;
  let raisedById = overrides?.raisedById;

  if (!customerId || !raisedById) {
    const { customer, user } = await createCustomer();
    if (!customerId) customerId = customer.id;
    if (!raisedById) raisedById = user.id;
  }

  const ticket = await prisma.ticket.create({
    data: {
      subject: overrides?.subject || 'Test Ticket',
      description: overrides?.description || 'Test description',
      status: overrides?.status || 'Open',
      priority: overrides?.priority || 'MEDIUM',
      customerId,
      raisedById,
      assignedToId: overrides?.assignedToId,
    },
    include: {
      customer: { include: { user: true } },
      raisedBy: true,
      assignedTo: true,
    },
  });

  return ticket;
};

export const createComment = async (overrides?: {
  ticketId?: string;
  userId?: string;
  content?: string;
  isInternal?: boolean;
}) => {
  let ticketId = overrides?.ticketId;
  let userId = overrides?.userId;

  if (!ticketId) {
    const ticket = await createTicket();
    ticketId = ticket.id;
  }

  if (!userId) {
    const { user } = await createAgent();
    userId = user.id;
  }

  const comment = await prisma.comment.create({
    data: {
      ticketId,
      userId,
      content: overrides?.content || 'Test comment',
      isInternal: overrides?.isInternal || false,
    },
    include: {
      user: true,
      ticket: true,
    },
  });

  return comment;
};
