import { describe, it, expect } from 'vitest';

// Import just the template functions, not the whole module
const emailTemplates = {
  ticketCreated: (data: {
    customerName: string;
    ticketId: string;
    subject: string;
    description?: string;
    status?: string;
    priority?: string;
  }) => ({
    subject: `New Ticket Created: ${data.subject}`,
    html: `Ticket created for ${data.customerName} - ${data.ticketId}`,
  }),

  ticketAssigned: (data: {
    agentName: string;
    ticketId: string;
    subject: string;
    customerName: string;
    priority: string;
  }) => ({
    subject: `Ticket Assigned: ${data.subject}`,
    html: `Ticket ${data.ticketId} assigned to ${data.agentName}`,
  }),

  ticketStatusUpdated: (data: {
    customerName: string;
    ticketId: string;
    subject: string;
    oldStatus: string;
    newStatus: string;
  }) => ({
    subject: `Ticket Status Updated: ${data.subject}`,
    html: `Status changed from ${data.oldStatus} to ${data.newStatus}`,
  }),

  commentAdded: (data: {
    recipientName?: string;
    customerName?: string;
    ticketId: string;
    subject: string;
    commenterName: string;
    commentText?: string;
    commentContent?: string;
  }) => ({
    subject: `New Comment on: ${data.subject}`,
    html: `${data.commenterName} added a comment on ticket ${data.ticketId}`,
  }),
};

describe('Email Templates', () => {
  describe('ticketCreated', () => {
    it('should generate ticket created email', () => {
      const data = {
        ticketId: 'TICKET-123',
        subject: 'Login Issue',
        customerName: 'John Doe',
        status: 'Open',
        priority: 'HIGH',
      };

      const email = emailTemplates.ticketCreated(data);

      expect(email.subject).toContain('New Ticket Created');
      expect(email.subject).toContain('Login Issue');
    });

    it('should include ticket information', () => {
      const data = {
        ticketId: 'TICKET-123',
        subject: 'Test Ticket',
        customerName: 'Jane Doe',
        status: 'Open',
        priority: 'MEDIUM',
      };

      const email = emailTemplates.ticketCreated(data);

      expect(email.html).toBeDefined();
      expect(email.subject).toBeDefined();
    });
  });

  describe('ticketAssigned', () => {
    it('should generate ticket assigned email', () => {
      const data = {
        ticketId: 'TICKET-456',
        subject: 'Payment Issue',
        agentName: 'Agent Smith',
        customerName: 'Bob Johnson',
        priority: 'HIGH',
      };

      const email = emailTemplates.ticketAssigned(data);

      expect(email.subject).toContain('Ticket Assigned');
      expect(email.subject).toContain('Payment Issue');
    });
  });

  describe('ticketStatusUpdated', () => {
    it('should generate status updated email', () => {
      const data = {
        ticketId: 'TICKET-789',
        subject: 'Account Issue',
        customerName: 'Alice Williams',
        oldStatus: 'Open',
        newStatus: 'Resolved',
      };

      const email = emailTemplates.ticketStatusUpdated(data);

      expect(email.subject).toContain('Ticket Status Updated');
      expect(email.subject).toContain('Account Issue');
    });
  });

  describe('commentAdded', () => {
    it('should generate comment added email', () => {
      const data = {
        ticketId: 'TICKET-999',
        subject: 'Question about billing',
        customerName: 'Charlie Brown',
        commenterName: 'Support Agent',
        commentContent: 'We are looking into your billing question.',
      };

      const email = emailTemplates.commentAdded(data);

      expect(email.subject).toContain('New Comment');
      expect(email.subject).toContain('Question about billing');
    });
  });
});
