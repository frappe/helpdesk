import { describe, it, expect } from 'vitest';
import request from 'supertest';
import express from 'express';
import ticketRoutes from '../../src/routes/ticket.routes.js';
import { errorHandler } from '../../src/middleware/errorHandler.js';
import { createUser, createAgent, createCustomer } from '../factories/userFactory.js';
import { createTicket } from '../factories/ticketFactory.js';
import { prisma } from '../setup.js';

// Create test Express app
const app = express();
app.use(express.json());
app.use('/tickets', ticketRoutes);
app.use(errorHandler);

// Helper to get auth token
async function getAuthToken(email: string, password: string) {
  const authApp = express();
  authApp.use(express.json());
  authApp.use('/auth', (await import('../../src/routes/auth.routes.js')).default);

  const response = await request(authApp)
    .post('/auth/login')
    .send({ email, password });

  return response.body.accessToken;
}

describe('TicketController', () => {
  describe('POST /tickets', () => {
    it('should create a ticket as customer', async () => {
      const password = 'Password123!';
      const { user, customer } = await createCustomer({ password });
      const token = await getAuthToken(user.email, password);

      const response = await request(app)
        .post('/tickets')
        .set('Authorization', `Bearer ${token}`)
        .send({
          subject: 'Test Ticket',
          description: 'This is a test ticket',
          priority: 'HIGH',
        });

      expect(response.status).toBe(201);
      expect(response.body.subject).toBe('Test Ticket');
      expect(response.body.customerId).toBe(customer.id);
      expect(response.body.status).toBe('Open');
    });

    it('should create a ticket as agent for a customer', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();
      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .post('/tickets')
        .set('Authorization', `Bearer ${token}`)
        .send({
          subject: 'Agent Created Ticket',
          description: 'Created by agent',
          customerId: customer.id,
          priority: 'MEDIUM',
        });

      expect(response.status).toBe(201);
      expect(response.body.customerId).toBe(customer.id);
    });

    it('should return 400 for missing subject', async () => {
      const password = 'Password123!';
      const { user } = await createCustomer({ password });
      const token = await getAuthToken(user.email, password);

      const response = await request(app)
        .post('/tickets')
        .set('Authorization', `Bearer ${token}`)
        .send({
          description: 'No subject provided',
        });

      expect(response.status).toBe(400);
    });

    it('should return 401 without authentication', async () => {
      const response = await request(app)
        .post('/tickets')
        .send({
          subject: 'Unauthorized Ticket',
          description: 'Should fail',
        });

      expect(response.status).toBe(401);
    });
  });

  describe('GET /tickets', () => {
    it('should list all tickets for agent', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();

      await createTicket({ customerId: customer.id });
      await createTicket({ customerId: customer.id });

      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .get('/tickets')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.data.length).toBeGreaterThanOrEqual(2);
      expect(response.body.pagination).toBeDefined();
    });

    it('should list only customer tickets for customer user', async () => {
      const password = 'Password123!';
      const { user: customer1User, customer: customer1 } = await createCustomer({ password });
      const { customer: customer2 } = await createCustomer();

      await createTicket({ customerId: customer1.id, raisedById: customer1User.id });
      await createTicket({ customerId: customer2.id });

      const token = await getAuthToken(customer1User.email, password);

      const response = await request(app)
        .get('/tickets')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.data.length).toBe(1);
      expect(response.body.data[0].customerId).toBe(customer1.id);
    });

    it('should filter tickets by status', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();

      await createTicket({ customerId: customer.id, status: 'Open' });
      await createTicket({ customerId: customer.id, status: 'Resolved' });

      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .get('/tickets?status=Open')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.data.every((t: any) => t.status === 'Open')).toBe(true);
    });

    it('should filter tickets by priority', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();

      await createTicket({ customerId: customer.id, priority: 'HIGH' });
      await createTicket({ customerId: customer.id, priority: 'LOW' });

      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .get('/tickets?priority=HIGH')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.data.every((t: any) => t.priority === 'HIGH')).toBe(true);
    });

    it('should search tickets by subject', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();

      await createTicket({ customerId: customer.id, subject: 'Login Issue' });
      await createTicket({ customerId: customer.id, subject: 'Payment Problem' });

      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .get('/tickets?search=Login')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.data.length).toBeGreaterThanOrEqual(1);
      expect(response.body.data.some((t: any) => t.subject.includes('Login'))).toBe(true);
    });

    it('should paginate results', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();

      // Create multiple tickets
      for (let i = 0; i < 15; i++) {
        await createTicket({ customerId: customer.id, subject: `Ticket ${i}` });
      }

      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .get('/tickets?page=1&limit=10')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.data.length).toBeLessThanOrEqual(10);
      expect(response.body.pagination.page).toBe(1);
      expect(response.body.pagination.limit).toBe(10);
    });
  });

  describe('GET /tickets/:id', () => {
    it('should get ticket details', async () => {
      const password = 'Password123!';
      const { user, customer } = await createCustomer({ password });
      const ticket = await createTicket({ customerId: customer.id, raisedById: user.id });
      const token = await getAuthToken(user.email, password);

      const response = await request(app)
        .get(`/tickets/${ticket.id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.id).toBe(ticket.id);
      expect(response.body.subject).toBe(ticket.subject);
      expect(response.body.customer).toBeDefined();
      expect(response.body.raisedBy).toBeDefined();
    });

    it('should return 404 for non-existent ticket', async () => {
      const password = 'Password123!';
      const { user } = await createAgent({ password });
      const token = await getAuthToken(user.email, password);

      const response = await request(app)
        .get('/tickets/non-existent-id')
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(404);
    });

    it('should return 403 when customer tries to access another customer ticket', async () => {
      const password = 'Password123!';
      const { user: customer1User, customer: customer1 } = await createCustomer({ password });
      const { customer: customer2 } = await createCustomer();
      const ticket = await createTicket({ customerId: customer2.id });

      const token = await getAuthToken(customer1User.email, password);

      const response = await request(app)
        .get(`/tickets/${ticket.id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(403);
    });

    it('should allow agent to access any ticket', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();
      const ticket = await createTicket({ customerId: customer.id });

      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .get(`/tickets/${ticket.id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(200);
      expect(response.body.id).toBe(ticket.id);
    });
  });

  describe('PATCH /tickets/:id', () => {
    it('should update ticket as agent', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();
      const ticket = await createTicket({ customerId: customer.id });
      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .patch(`/tickets/${ticket.id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          subject: 'Updated Subject',
          status: 'Resolved',
          priority: 'HIGH',
        });

      expect(response.status).toBe(200);
      expect(response.body.subject).toBe('Updated Subject');
      expect(response.body.status).toBe('Resolved');
      expect(response.body.priority).toBe('HIGH');
    });

    it('should prevent customer from changing status', async () => {
      const password = 'Password123!';
      const { user, customer } = await createCustomer({ password });
      const ticket = await createTicket({ customerId: customer.id, raisedById: user.id, status: 'Open' });
      const token = await getAuthToken(user.email, password);

      const response = await request(app)
        .patch(`/tickets/${ticket.id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          status: 'Resolved', // Should be ignored
        });

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('Open'); // Should remain Open
    });

    it('should create activity log for updates', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();
      const ticket = await createTicket({ customerId: customer.id });
      const token = await getAuthToken(agentUser.email, password);

      await request(app)
        .patch(`/tickets/${ticket.id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          status: 'Resolved',
        });

      const activities = await prisma.activity.findMany({
        where: { ticketId: ticket.id, action: 'updated' },
      });

      expect(activities.length).toBeGreaterThan(0);
    });
  });

  describe('DELETE /tickets/:id', () => {
    it('should delete ticket as admin', async () => {
      const password = 'Password123!';
      const { user: adminUser } = await createUser({ password, userType: 'ADMIN' });
      const { customer } = await createCustomer();
      const ticket = await createTicket({ customerId: customer.id });
      const token = await getAuthToken(adminUser.email, password);

      const response = await request(app)
        .delete(`/tickets/${ticket.id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(204);

      const deletedTicket = await prisma.ticket.findUnique({
        where: { id: ticket.id },
      });
      expect(deletedTicket).toBeNull();
    });

    it('should return 403 when non-admin tries to delete', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();
      const ticket = await createTicket({ customerId: customer.id });
      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .delete(`/tickets/${ticket.id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(response.status).toBe(403);
    });
  });

  describe('POST /tickets/:id/comments', () => {
    it('should add comment to ticket', async () => {
      const password = 'Password123!';
      const { user, customer } = await createCustomer({ password });
      const ticket = await createTicket({ customerId: customer.id, raisedById: user.id });
      const token = await getAuthToken(user.email, password);

      const response = await request(app)
        .post(`/tickets/${ticket.id}/comments`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          content: 'This is a test comment',
        });

      expect(response.status).toBe(201);
      expect(response.body.content).toBe('This is a test comment');
      expect(response.body.ticketId).toBe(ticket.id);
    });

    it('should create internal comment as agent', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { customer } = await createCustomer();
      const ticket = await createTicket({ customerId: customer.id });
      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .post(`/tickets/${ticket.id}/comments`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          content: 'Internal note',
          isInternal: true,
        });

      expect(response.status).toBe(201);
      expect(response.body.isInternal).toBe(true);
    });

    it('should prevent customer from creating internal comments', async () => {
      const password = 'Password123!';
      const { user, customer } = await createCustomer({ password });
      const ticket = await createTicket({ customerId: customer.id, raisedById: user.id });
      const token = await getAuthToken(user.email, password);

      const response = await request(app)
        .post(`/tickets/${ticket.id}/comments`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          content: 'Trying to make internal comment',
          isInternal: true, // Should be ignored
        });

      expect(response.status).toBe(201);
      expect(response.body.isInternal).toBe(false);
    });
  });

  describe('PATCH /tickets/:id/assign', () => {
    it('should assign ticket to agent', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { user: assigneeUser } = await createAgent();
      const { customer } = await createCustomer();
      const ticket = await createTicket({ customerId: customer.id });
      const token = await getAuthToken(agentUser.email, password);

      const response = await request(app)
        .patch(`/tickets/${ticket.id}/assign`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          assignedToId: assigneeUser.id,
        });

      expect(response.status).toBe(200);
      expect(response.body.assignedToId).toBe(assigneeUser.id);
    });

    it('should return 403 when customer tries to assign', async () => {
      const password = 'Password123!';
      const { user, customer } = await createCustomer({ password });
      const { user: agentUser } = await createAgent();
      const ticket = await createTicket({ customerId: customer.id, raisedById: user.id });
      const token = await getAuthToken(user.email, password);

      const response = await request(app)
        .patch(`/tickets/${ticket.id}/assign`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          assignedToId: agentUser.id,
        });

      expect(response.status).toBe(403);
    });

    it('should create activity log for assignment', async () => {
      const password = 'Password123!';
      const { user: agentUser } = await createAgent({ password });
      const { user: assigneeUser } = await createAgent();
      const { customer } = await createCustomer();
      const ticket = await createTicket({ customerId: customer.id });
      const token = await getAuthToken(agentUser.email, password);

      await request(app)
        .patch(`/tickets/${ticket.id}/assign`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          assignedToId: assigneeUser.id,
        });

      const activities = await prisma.activity.findMany({
        where: { ticketId: ticket.id, action: 'assigned' },
      });

      expect(activities.length).toBe(1);
    });
  });
});
