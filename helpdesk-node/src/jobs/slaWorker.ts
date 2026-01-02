import { slaQueue } from './queue.js';
import { prisma } from '../utils/prisma.js';
import { logger } from '../utils/logger.js';
import { addMinutes, isPast } from 'date-fns';

// SLA job types
export enum SLAJobType {
  CHECK_SLA_BREACH = 'check-sla-breach',
  AUTO_CLOSE_TICKETS = 'auto-close-tickets',
}

// Check for SLA breaches
slaQueue.process('check-sla-breach', async () => {
  logger.info('Checking for SLA breaches...');

  const tickets = await prisma.ticket.findMany({
    where: {
      status: { not: 'Closed' },
      OR: [
        { responseBy: { not: null } },
        { resolutionBy: { not: null } },
      ],
    },
    include: {
      customer: { include: { user: true } },
      assignedTo: true,
    },
  });

  const now = new Date();
  let breachCount = 0;

  for (const ticket of tickets) {
    // Check response SLA
    if (
      ticket.responseBy &&
      !ticket.firstRespondedOn &&
      isPast(ticket.responseBy)
    ) {
      logger.warn(`Ticket ${ticket.id} has breached response SLA`);
      breachCount++;

      // You can add notification logic here
      await prisma.notification.create({
        data: {
          userId: ticket.assignedToId || ticket.raisedById,
          title: 'SLA Breach',
          message: `Ticket #${ticket.id} has breached response SLA`,
          type: 'sla_breach',
          link: `/tickets/${ticket.id}`,
        },
      });
    }

    // Check resolution SLA
    if (
      ticket.resolutionBy &&
      !ticket.resolutionDate &&
      isPast(ticket.resolutionBy)
    ) {
      logger.warn(`Ticket ${ticket.id} has breached resolution SLA`);
      breachCount++;

      await prisma.notification.create({
        data: {
          userId: ticket.assignedToId || ticket.raisedById,
          title: 'SLA Breach',
          message: `Ticket #${ticket.id} has breached resolution SLA`,
          type: 'sla_breach',
          link: `/tickets/${ticket.id}`,
        },
      });
    }
  }

  logger.info(`SLA check complete. Found ${breachCount} breaches.`);
});

// Auto-close resolved tickets after X days
slaQueue.process('auto-close-tickets', async () => {
  logger.info('Auto-closing resolved tickets...');

  const closureThresholdDays = 7; // Close after 7 days
  const thresholdDate = addMinutes(new Date(), -closureThresholdDays * 24 * 60);

  const ticketsToClose = await prisma.ticket.findMany({
    where: {
      status: 'Resolved',
      resolutionDate: {
        lte: thresholdDate,
      },
    },
  });

  for (const ticket of ticketsToClose) {
    await prisma.ticket.update({
      where: { id: ticket.id },
      data: { status: 'Closed' },
    });

    logger.info(`Auto-closed ticket ${ticket.id}`);
  }

  logger.info(`Auto-closed ${ticketsToClose.length} tickets`);
});

// Schedule recurring jobs
export const scheduleSLAJobs = () => {
  // Check SLA breaches every 15 minutes
  slaQueue.add(
    'check-sla-breach',
    {},
    {
      repeat: {
        cron: '*/15 * * * *', // Every 15 minutes
      },
    }
  );

  // Auto-close tickets daily at 2 AM
  slaQueue.add(
    'auto-close-tickets',
    {},
    {
      repeat: {
        cron: '0 2 * * *', // Daily at 2 AM
      },
    }
  );

  logger.info('⏰ SLA jobs scheduled');
};

logger.info('📊 SLA worker started');
