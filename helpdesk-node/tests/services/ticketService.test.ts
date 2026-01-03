import { describe, it, expect, beforeEach, vi } from 'vitest';
import { TicketService } from '../../src/services/ticketService.js';
import { createTicket, createComment } from '../factories/ticketFactory.js';
import { createCustomer, createAgent } from '../factories/userFactory.js';
import { NotFoundError, ForbiddenError } from '../../src/utils/errors.js';
import { prisma } from '../setup.js';

// Mock socket events
vi.mock('../../src/utils/socket.js', () => ({
  emitTicketCreated: vi.fn(),
  emitTicketUpdated: vi.fn(),
  emitTicketAssigned: vi.fn(),
  emitCommentAdded: vi.fn(),
}));

describe('TicketService', () => {
  let ticketService: TicketService;

  beforeEach(() => {
    ticketService = new TicketService();
  });

  describe('createTicket', () => {
    it('should create a ticket successfully', async () => {
      const { user, customer } = await createCustomer();

      const ticket = await ticketService.createTicket({
        subject: 'Test Ticket',
        description: 'Test description',
        priority: 'HIGH',
        customerId: customer.id,
        raisedById: user.id,
      });

      expect(ticket).toBeDefined();
      expect(ticket.subject).toBe('Test Ticket');
      expect(ticket.priority).toBe('HIGH');
      expect(ticket.status).toBe('Open');
      expect(ticket.customerId).toBe(customer.id);
    });

    it('should auto-assign customer if not provided', async () => {
      const { user, customer } = await createCustomer();

      const ticket = await ticketService.createTicket({
        subject: 'Auto Customer',
        raisedById: user.id,
      });

      expect(ticket.customerId).toBe(customer.id);
    });

    it('should log activity after ticket creation', async () => {
      const { user, customer } = await createCustomer();

      const ticket = await ticketService.createTicket({
        subject: 'Activity Test',
        customerId: customer.id,
        raisedById: user.id,
      });

      const activity = await prisma.activity.findFirst({
        where: { ticketId: ticket.id },
      });

      expect(activity).toBeDefined();
      expect(activity?.action).toBe('created');
    });
  });

  describe('listTickets', () => {
    it('should list all tickets for agent', async () => {
      const { user: agentUser } = await createAgent();

      await createTicket();
      await createTicket();
      await createTicket();

      const result = await ticketService.listTickets(
        { page: 1, limit: 10 },
        agentUser.id,
        'AGENT'
      );

      expect(result.data.length).toBe(3);
      expect(result.pagination.total).toBe(3);
    });

    it('should filter tickets by customer for customer users', async () => {
      const { user: customer1User, customer: customer1 } = await createCustomer();
      const { customer: customer2 } = await createCustomer();

      // Create tickets for both customers
      await createTicket({ customerId: customer1.id, raisedById: customer1User.id });
      await createTicket({ customerId: customer2.id });

      const result = await ticketService.listTickets(
        {},
        customer1User.id,
        'CUSTOMER'
      );

      expect(result.data.length).toBe(1);
      expect(result.data[0].customerId).toBe(customer1.id);
    });

    it('should filter tickets by status', async () => {
      const { user } = await createAgent();

      await createTicket({ status: 'Open' });
      await createTicket({ status: 'Resolved' });
      await createTicket({ status: 'Open' });

      const result = await ticketService.listTickets(
        { status: 'Open' },
        user.id,
        'AGENT'
      );

      expect(result.data.length).toBe(2);
      expect(result.data.every((t) => t.status === 'Open')).toBe(true);
    });

    it('should filter tickets by priority', async () => {
      const { user } = await createAgent();

      await createTicket({ priority: 'HIGH' });
      await createTicket({ priority: 'LOW' });
      await createTicket({ priority: 'HIGH' });

      const result = await ticketService.listTickets(
        { priority: 'HIGH' },
        user.id,
        'AGENT'
      );

      expect(result.data.length).toBe(2);
      expect(result.data.every((t) => t.priority === 'HIGH')).toBe(true);
    });

    it('should paginate results correctly', async () => {
      const { user } = await createAgent();

      // Create 5 tickets
      for (let i = 0; i < 5; i++) {
        await createTicket();
      }

      const page1 = await ticketService.listTickets(
        { page: 1, limit: 2 },
        user.id,
        'AGENT'
      );

      expect(page1.data.length).toBe(2);
      expect(page1.pagination.page).toBe(1);
      expect(page1.pagination.totalPages).toBe(3);

      const page2 = await ticketService.listTickets(
        { page: 2, limit: 2 },
        user.id,
        'AGENT'
      );

      expect(page2.data.length).toBe(2);
      expect(page2.pagination.page).toBe(2);
    });

    it('should search tickets by subject', async () => {
      const { user } = await createAgent();

      await createTicket({ subject: 'Login Issue' });
      await createTicket({ subject: 'Payment Problem' });
      await createTicket({ subject: 'Login Error' });

      const result = await ticketService.listTickets(
        { search: 'login' },
        user.id,
        'AGENT'
      );

      expect(result.data.length).toBe(2);
    });
  });

  describe('getTicket', () => {
    it('should get ticket with all details', async () => {
      const { user } = await createAgent();
      const ticket = await createTicket();

      const result = await ticketService.getTicket(ticket.id, user.id, 'AGENT');

      expect(result).toBeDefined();
      expect(result.id).toBe(ticket.id);
      expect(result.customer).toBeDefined();
      expect(result.comments).toBeDefined();
      expect(result.activities).toBeDefined();
    });

    it('should throw NotFoundError for non-existent ticket', async () => {
      const { user } = await createAgent();

      await expect(
        ticketService.getTicket('non-existent-id', user.id, 'AGENT')
      ).rejects.toThrow(NotFoundError);
    });

    it('should throw ForbiddenError when customer tries to access other customer ticket', async () => {
      const { user: customer1User } = await createCustomer();
      const { customer: customer2 } = await createCustomer();

      const ticket = await createTicket({ customerId: customer2.id });

      await expect(
        ticketService.getTicket(ticket.id, customer1User.id, 'CUSTOMER')
      ).rejects.toThrow(ForbiddenError);
    });
  });

  describe('updateTicket', () => {
    it('should update ticket successfully', async () => {
      const { user } = await createAgent();
      const ticket = await createTicket();

      const updated = await ticketService.updateTicket(
        ticket.id,
        { subject: 'Updated Subject', status: 'Resolved' },
        user.id,
        'AGENT'
      );

      expect(updated.subject).toBe('Updated Subject');
      expect(updated.status).toBe('Resolved');
    });

    it('should log activities for changed fields', async () => {
      const { user } = await createAgent();
      const ticket = await createTicket();

      await ticketService.updateTicket(
        ticket.id,
        { status: 'Resolved', priority: 'HIGH' },
        user.id,
        'AGENT'
      );

      const activities = await prisma.activity.findMany({
        where: { ticketId: ticket.id, action: 'updated' },
      });

      expect(activities.length).toBeGreaterThanOrEqual(2);
    });

    it('should prevent customers from updating status', async () => {
      const { user, customer } = await createCustomer();
      const ticket = await createTicket({
        customerId: customer.id,
        raisedById: user.id,
      });

      const updated = await ticketService.updateTicket(
        ticket.id,
        { status: 'Resolved' }, // This should be ignored
        user.id,
        'CUSTOMER'
      );

      expect(updated.status).not.toBe('Resolved');
    });
  });

  describe('addComment', () => {
    it('should add comment to ticket', async () => {
      const { user } = await createAgent();
      const ticket = await createTicket();

      const comment = await ticketService.addComment(
        ticket.id,
        user.id,
        'This is a comment',
        false
      );

      expect(comment).toBeDefined();
      expect(comment.content).toBe('This is a comment');
      expect(comment.ticketId).toBe(ticket.id);
      expect(comment.isInternal).toBe(false);
    });

    it('should throw NotFoundError for non-existent ticket', async () => {
      const { user } = await createAgent();

      await expect(
        ticketService.addComment('non-existent-id', user.id, 'Comment')
      ).rejects.toThrow(NotFoundError);
    });

    it('should support internal comments', async () => {
      const { user } = await createAgent();
      const ticket = await createTicket();

      const comment = await ticketService.addComment(
        ticket.id,
        user.id,
        'Internal note',
        true
      );

      expect(comment.isInternal).toBe(true);
    });
  });

  describe('assignTicket', () => {
    it('should assign ticket to agent', async () => {
      const { user: agentUser } = await createAgent();
      const ticket = await createTicket();

      const updated = await ticketService.assignTicket(
        ticket.id,
        agentUser.id,
        agentUser.id
      );

      expect(updated.assignedToId).toBe(agentUser.id);
    });

    it('should log assignment activity', async () => {
      const { user: agentUser } = await createAgent();
      const ticket = await createTicket();

      await ticketService.assignTicket(ticket.id, agentUser.id, agentUser.id);

      const activity = await prisma.activity.findFirst({
        where: {
          ticketId: ticket.id,
          fieldName: 'assignedToId',
        },
      });

      expect(activity).toBeDefined();
      expect(activity?.newValue).toBe(agentUser.id);
    });
  });

  describe('deleteTicket', () => {
    it('should delete ticket as admin', async () => {
      const ticket = await createTicket();

      await ticketService.deleteTicket(ticket.id, 'admin-user-id', 'ADMIN');

      const deleted = await prisma.ticket.findUnique({
        where: { id: ticket.id },
      });

      expect(deleted).toBeNull();
    });

    it('should throw ForbiddenError for non-admin users', async () => {
      const { user } = await createAgent();
      const ticket = await createTicket();

      await expect(
        ticketService.deleteTicket(ticket.id, user.id, 'AGENT')
      ).rejects.toThrow(ForbiddenError);
    });
  });
});
