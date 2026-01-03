import { describe, it, expect, beforeEach } from 'vitest';
import { SearchService } from '../../src/services/searchService.js';
import { createTicket } from '../factories/ticketFactory.js';
import { createArticle } from '../factories/articleFactory.js';
import { createAgent, createCustomer } from '../factories/userFactory.js';

describe('SearchService', () => {
  let searchService: SearchService;

  beforeEach(() => {
    searchService = new SearchService();
  });

  describe('searchTickets', () => {
    it('should search tickets by subject', async () => {
      const { user } = await createAgent();

      await createTicket({ subject: 'Login Problem' });
      await createTicket({ subject: 'Payment Issue' });
      await createTicket({ subject: 'Login Error' });

      const results = await searchService.searchTickets(
        'login',
        user.id,
        'AGENT'
      );

      expect(results.length).toBe(2);
      expect(results.every((t) => t.subject.toLowerCase().includes('login'))).toBe(
        true
      );
    });

    it('should search tickets by description', async () => {
      const { user } = await createAgent();

      await createTicket({ description: 'Cannot access my account' });
      await createTicket({ description: 'Payment failed' });
      await createTicket({ description: 'Account locked' });

      const results = await searchService.searchTickets(
        'account',
        user.id,
        'AGENT'
      );

      expect(results.length).toBe(2);
    });

    it('should search tickets by ID', async () => {
      const { user } = await createAgent();
      const ticket = await createTicket();

      const results = await searchService.searchTickets(
        ticket.id.substring(0, 8),
        user.id,
        'AGENT'
      );

      expect(results.length).toBeGreaterThanOrEqual(1);
      expect(results.some((t) => t.id === ticket.id)).toBe(true);
    });

    it('should filter results by status', async () => {
      const { user } = await createAgent();

      await createTicket({ subject: 'Test 1', status: 'Open' });
      await createTicket({ subject: 'Test 2', status: 'Resolved' });
      await createTicket({ subject: 'Test 3', status: 'Open' });

      const results = await searchService.searchTickets('test', user.id, 'AGENT', {
        status: 'Open',
      });

      expect(results.length).toBe(2);
      expect(results.every((t) => t.status === 'Open')).toBe(true);
    });

    it('should filter results by priority', async () => {
      const { user } = await createAgent();

      await createTicket({ subject: 'Issue 1', priority: 'HIGH' });
      await createTicket({ subject: 'Issue 2', priority: 'LOW' });
      await createTicket({ subject: 'Issue 3', priority: 'HIGH' });

      const results = await searchService.searchTickets('issue', user.id, 'AGENT', {
        priority: 'HIGH',
      });

      expect(results.length).toBe(2);
    });

    it('should limit results', async () => {
      const { user } = await createAgent();

      for (let i = 0; i < 25; i++) {
        await createTicket({ subject: `Ticket ${i}` });
      }

      const results = await searchService.searchTickets('ticket', user.id, 'AGENT', {
        limit: 10,
      });

      expect(results.length).toBe(10);
    });

    it('should only return customer own tickets', async () => {
      const { user: customer1User, customer: customer1 } = await createCustomer();
      const { customer: customer2 } = await createCustomer();

      await createTicket({ subject: 'Customer 1 Ticket', customerId: customer1.id });
      await createTicket({ subject: 'Customer 2 Ticket', customerId: customer2.id });

      const results = await searchService.searchTickets(
        'ticket',
        customer1User.id,
        'CUSTOMER'
      );

      expect(results.length).toBe(1);
      expect(results[0].customerId).toBe(customer1.id);
    });
  });

  describe('searchArticles', () => {
    it('should search articles by title', async () => {
      await createArticle({ title: 'How to Login', isPublished: true });
      await createArticle({ title: 'Payment Guide', isPublished: true });
      await createArticle({ title: 'Login Issues', isPublished: true });

      const results = await searchService.searchArticles('login');

      expect(results.length).toBe(2);
    });

    it('should search articles by content', async () => {
      await createArticle({
        title: 'Article 1',
        content: 'This article explains authentication',
        isPublished: true,
      });
      await createArticle({
        title: 'Article 2',
        content: 'This covers payments',
        isPublished: true,
      });

      const results = await searchService.searchArticles('authentication');

      expect(results.length).toBe(1);
    });

    it('should only return published articles', async () => {
      await createArticle({ title: 'Published Guide', isPublished: true });
      await createArticle({ title: 'Draft Guide', isPublished: false });

      const results = await searchService.searchArticles('guide');

      expect(results.length).toBe(1);
      expect(results[0].isPublished).toBe(true);
    });

    it('should order by views and recency', async () => {
      const article1 = await createArticle({
        title: 'Popular Article',
        isPublished: true,
      });
      await createArticle({ title: 'New Article', isPublished: true });

      // Increment views for article1
      await searchService.searchArticles('');
      await searchService.searchArticles('');

      const results = await searchService.searchArticles('article');

      // Popular article should come first
      expect(results[0].title).toBe('Popular Article');
    });
  });

  describe('searchCustomers', () => {
    it('should search customers by name', async () => {
      await createCustomer({ customerName: 'John Doe' });
      await createCustomer({ customerName: 'Jane Smith' });
      await createCustomer({ customerName: 'John Williams' });

      const results = await searchService.searchCustomers('john');

      expect(results.length).toBe(2);
    });

    it('should search customers by email', async () => {
      await createCustomer({ email: 'john@example.com' });
      await createCustomer({ email: 'jane@test.com' });

      const results = await searchService.searchCustomers('example');

      expect(results.length).toBe(1);
      expect(results[0].user.email).toContain('example');
    });

    it('should include ticket count', async () => {
      const { customer } = await createCustomer();
      await createTicket({ customerId: customer.id });
      await createTicket({ customerId: customer.id });

      const results = await searchService.searchCustomers(customer.customerName);

      expect(results[0]._count.tickets).toBe(2);
    });
  });

  describe('globalSearch', () => {
    it('should search across all entities', async () => {
      const { user: agentUser } = await createAgent();

      await createTicket({ subject: 'Login Ticket' });
      await createArticle({ title: 'Login Guide', isPublished: true });
      await createCustomer({ customerName: 'Login Support' });

      const results = await searchService.globalSearch(
        'login',
        agentUser.id,
        'AGENT'
      );

      expect(results.tickets.length).toBeGreaterThan(0);
      expect(results.articles.length).toBeGreaterThan(0);
      expect(results.customers.length).toBeGreaterThan(0);
      expect(results.total).toBeGreaterThan(0);
    });

    it('should limit results per entity to 10', async () => {
      const { user: agentUser } = await createAgent();

      // Create 15 tickets
      for (let i = 0; i < 15; i++) {
        await createTicket({ subject: `Search Test ${i}` });
      }

      const results = await searchService.globalSearch(
        'search',
        agentUser.id,
        'AGENT'
      );

      expect(results.tickets.length).toBe(10);
    });

    it('should not return customers for customer users', async () => {
      const { user: customerUser } = await createCustomer();

      const results = await searchService.globalSearch(
        'test',
        customerUser.id,
        'CUSTOMER'
      );

      expect(results.customers).toEqual([]);
    });
  });
});
