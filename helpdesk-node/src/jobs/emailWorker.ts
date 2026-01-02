import { emailQueue } from './queue.js';
import { emailService } from '../services/emailService.js';
import { logger } from '../utils/logger.js';

// Email job types
export enum EmailJobType {
  TICKET_CREATED = 'ticket-created',
  TICKET_ASSIGNED = 'ticket-assigned',
  TICKET_STATUS_UPDATED = 'ticket-status-updated',
  COMMENT_ADDED = 'comment-added',
}

interface TicketCreatedJob {
  type: EmailJobType.TICKET_CREATED;
  ticketId: string;
}

interface TicketAssignedJob {
  type: EmailJobType.TICKET_ASSIGNED;
  ticketId: string;
  agentId: string;
}

interface TicketStatusUpdatedJob {
  type: EmailJobType.TICKET_STATUS_UPDATED;
  ticketId: string;
  oldStatus: string;
  newStatus: string;
}

interface CommentAddedJob {
  type: EmailJobType.COMMENT_ADDED;
  commentId: string;
}

type EmailJob =
  | TicketCreatedJob
  | TicketAssignedJob
  | TicketStatusUpdatedJob
  | CommentAddedJob;

// Process email jobs
emailQueue.process(async (job) => {
  const data = job.data as EmailJob;

  logger.info(`Processing email job: ${data.type}`);

  switch (data.type) {
    case EmailJobType.TICKET_CREATED:
      await emailService.sendTicketCreatedEmail(data.ticketId);
      break;

    case EmailJobType.TICKET_ASSIGNED:
      await emailService.sendTicketAssignedEmail(data.ticketId, data.agentId);
      break;

    case EmailJobType.TICKET_STATUS_UPDATED:
      await emailService.sendTicketStatusUpdatedEmail(
        data.ticketId,
        data.oldStatus,
        data.newStatus
      );
      break;

    case EmailJobType.COMMENT_ADDED:
      await emailService.sendCommentAddedEmail(data.commentId);
      break;

    default:
      logger.error(`Unknown email job type: ${(data as any).type}`);
  }
});

// Helper functions to queue email jobs
export const queueTicketCreatedEmail = async (ticketId: string) => {
  await emailQueue.add(
    { type: EmailJobType.TICKET_CREATED, ticketId },
    { attempts: 3, backoff: { type: 'exponential', delay: 2000 } }
  );
};

export const queueTicketAssignedEmail = async (ticketId: string, agentId: string) => {
  await emailQueue.add(
    { type: EmailJobType.TICKET_ASSIGNED, ticketId, agentId },
    { attempts: 3, backoff: { type: 'exponential', delay: 2000 } }
  );
};

export const queueTicketStatusUpdatedEmail = async (
  ticketId: string,
  oldStatus: string,
  newStatus: string
) => {
  await emailQueue.add(
    { type: EmailJobType.TICKET_STATUS_UPDATED, ticketId, oldStatus, newStatus },
    { attempts: 3, backoff: { type: 'exponential', delay: 2000 } }
  );
};

export const queueCommentAddedEmail = async (commentId: string) => {
  await emailQueue.add(
    { type: EmailJobType.COMMENT_ADDED, commentId },
    { attempts: 3, backoff: { type: 'exponential', delay: 2000 } }
  );
};

logger.info('✉️  Email worker started');
