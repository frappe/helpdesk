import { sendEmail, emailTemplates } from '../utils/email.js';
import { prisma } from '../utils/prisma.js';
import { logger } from '../utils/logger.js';

export class EmailService {
  async sendTicketCreatedEmail(ticketId: string) {
    try {
      const ticket = await prisma.ticket.findUnique({
        where: { id: ticketId },
        include: {
          customer: { include: { user: true } },
        },
      });

      if (!ticket || !ticket.customer.user.email) {
        return;
      }

      const template = emailTemplates.ticketCreated({
        customerName: ticket.customer.user.fullName,
        ticketId: ticket.id,
        subject: ticket.subject,
        description: ticket.description || '',
      });

      await sendEmail({
        to: ticket.customer.user.email,
        subject: template.subject,
        html: template.html,
        text: template.text,
      });

      logger.info(`Ticket created email sent to ${ticket.customer.user.email}`);
    } catch (error) {
      logger.error('Failed to send ticket created email:', error);
    }
  }

  async sendTicketAssignedEmail(ticketId: string, agentId: string) {
    try {
      const [ticket, agent] = await Promise.all([
        prisma.ticket.findUnique({
          where: { id: ticketId },
          include: {
            customer: { include: { user: true } },
          },
        }),
        prisma.agent.findUnique({
          where: { id: agentId },
          include: { user: true },
        }),
      ]);

      if (!ticket || !agent || !agent.user.email) {
        return;
      }

      const template = emailTemplates.ticketAssigned({
        agentName: agent.user.fullName,
        ticketId: ticket.id,
        subject: ticket.subject,
        customerName: ticket.customer.user.fullName,
        priority: ticket.priority || 'MEDIUM',
      });

      await sendEmail({
        to: agent.user.email,
        subject: template.subject,
        html: template.html,
        text: template.text,
      });

      logger.info(`Ticket assigned email sent to ${agent.user.email}`);
    } catch (error) {
      logger.error('Failed to send ticket assigned email:', error);
    }
  }

  async sendTicketStatusUpdatedEmail(
    ticketId: string,
    oldStatus: string,
    newStatus: string
  ) {
    try {
      const ticket = await prisma.ticket.findUnique({
        where: { id: ticketId },
        include: {
          customer: { include: { user: true } },
        },
      });

      if (!ticket || !ticket.customer.user.email) {
        return;
      }

      const template = emailTemplates.ticketStatusUpdated({
        customerName: ticket.customer.user.fullName,
        ticketId: ticket.id,
        subject: ticket.subject,
        oldStatus,
        newStatus,
      });

      await sendEmail({
        to: ticket.customer.user.email,
        subject: template.subject,
        html: template.html,
        text: template.text,
      });

      logger.info(`Ticket status updated email sent to ${ticket.customer.user.email}`);
    } catch (error) {
      logger.error('Failed to send ticket status updated email:', error);
    }
  }

  async sendCommentAddedEmail(commentId: string) {
    try {
      const comment = await prisma.comment.findUnique({
        where: { id: commentId },
        include: {
          ticket: {
            include: {
              customer: { include: { user: true } },
              assignedTo: true,
            },
          },
          user: true,
        },
      });

      if (!comment || comment.isInternal) {
        return; // Don't send email for internal comments
      }

      // Determine recipient (send to customer if agent commented, or to agent if customer commented)
      let recipientEmail: string;
      let recipientName: string;

      if (comment.user.userType === 'AGENT' && comment.ticket.customer.user.email) {
        // Agent commented - notify customer
        recipientEmail = comment.ticket.customer.user.email;
        recipientName = comment.ticket.customer.user.fullName;
      } else if (
        comment.user.userType === 'CUSTOMER' &&
        comment.ticket.assignedTo?.email
      ) {
        // Customer commented - notify assigned agent
        recipientEmail = comment.ticket.assignedTo.email;
        recipientName = comment.ticket.assignedTo.fullName;
      } else {
        return; // No recipient to notify
      }

      const template = emailTemplates.commentAdded({
        recipientName,
        ticketId: comment.ticket.id,
        subject: comment.ticket.subject,
        commenterName: comment.user.fullName,
        commentText: comment.content,
      });

      await sendEmail({
        to: recipientEmail,
        subject: template.subject,
        html: template.html,
        text: template.text,
      });

      logger.info(`Comment added email sent to ${recipientEmail}`);
    } catch (error) {
      logger.error('Failed to send comment added email:', error);
    }
  }
}

export const emailService = new EmailService();
