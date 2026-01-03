import { describe, it, expect, beforeEach } from 'vitest';
import { DashboardService } from '../../src/services/dashboardService.js';
import { createTicket } from '../factories/ticketFactory.js';
import { createAgent, createCustomer } from '../factories/userFactory.js';
import { prisma } from '../setup.js';
import { subDays } from 'date-fns';

describe('DashboardService', () => {
  let dashboardService: DashboardService;

  beforeEach(() => {
    dashboardService = new DashboardService();
  });

  describe('getDashboardMetrics', () => {
    it('should return correct ticket counts for agent', async () => {
      const { user: agentUser } = await createAgent();

      // Create tickets with different statuses
      await createTicket({ status: 'Open', assignedToId: agentUser.id });
      await createTicket({ status: 'Open', assignedToId: agentUser.id });
      await createTicket({ status: 'Resolved', assignedToId: agentUser.id });
      await createTicket({ status: 'Closed', assignedToId: agentUser.id });

      const metrics = await dashboardService.getDashboardMetrics(
        agentUser.id,
        'AGENT'
      );

      expect(metrics.totalTickets).toBe(4);
      expect(metrics.openTickets).toBe(2);
      expect(metrics.resolvedTickets).toBe(1);
      expect(metrics.closedTickets).toBe(1);
    });

    it('should return correct ticket counts for customer', async () => {
      const { user: customer1User, customer: customer1 } = await createCustomer();
      const { customer: customer2 } = await createCustomer();

      // Create tickets for both customers
      await createTicket({ customerId: customer1.id, status: 'Open' });
      await createTicket({ customerId: customer1.id, status: 'Resolved' });
      await createTicket({ customerId: customer2.id, status: 'Open' });

      const metrics = await dashboardService.getDashboardMetrics(
        customer1User.id,
        'CUSTOMER'
      );

      expect(metrics.totalTickets).toBe(2);
      expect(metrics.openTickets).toBe(1);
      expect(metrics.resolvedTickets).toBe(1);
    });

    it('should calculate average response time correctly', async () => {
      const { user: agentUser } = await createAgent();

      // Create ticket with response time
      const now = new Date();
      const createdTime = subDays(now, 1); // 1 day ago

      const ticket = await prisma.ticket.create({
        data: {
          subject: 'Response Time Test',
          status: 'Open',
          priority: 'MEDIUM',
          customerId: (await createCustomer()).customer.id,
          raisedById: (await createCustomer()).user.id,
          assignedToId: agentUser.id,
          createdAt: createdTime,
          firstRespondedOn: now, // Responded after 24 hours
        },
      });

      const metrics = await dashboardService.getDashboardMetrics(
        agentUser.id,
        'AGENT'
      );

      expect(metrics.avgResponseTime).toBeCloseTo(24, 0); // ~24 hours
    });

    it('should return only recent tickets in recentTickets array', async () => {
      const { user: agentUser } = await createAgent();

      // Create old ticket
      await prisma.ticket.create({
        data: {
          subject: 'Old Ticket',
          status: 'Open',
          priority: 'MEDIUM',
          customerId: (await createCustomer()).customer.id,
          raisedById: (await createCustomer()).user.id,
          assignedToId: agentUser.id,
          createdAt: subDays(new Date(), 40), // 40 days ago
        },
      });

      // Create recent ticket
      await createTicket({ assignedToId: agentUser.id });

      const metrics = await dashboardService.getDashboardMetrics(
        agentUser.id,
        'AGENT'
      );

      expect(metrics.recentTickets.length).toBe(1);
      expect(metrics.recentTickets[0].subject).not.toBe('Old Ticket');
    });

    it('should limit recent tickets to 10', async () => {
      const { user: agentUser } = await createAgent();

      // Create 15 tickets
      for (let i = 0; i < 15; i++) {
        await createTicket({ assignedToId: agentUser.id });
      }

      const metrics = await dashboardService.getDashboardMetrics(
        agentUser.id,
        'AGENT'
      );

      expect(metrics.recentTickets.length).toBe(10);
    });
  });
});
