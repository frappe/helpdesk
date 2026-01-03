import { prisma } from '../utils/prisma.js';
import { subDays } from 'date-fns';

export class DashboardService {
  async getDashboardMetrics(userId: string, userType: string) {
    const thirtyDaysAgo = subDays(new Date(), 30);

    // Base filters
    let ticketFilter: any = {};

    if (userType === 'AGENT') {
      ticketFilter.assignedToId = userId;
    } else if (userType === 'CUSTOMER') {
      const customer = await prisma.customer.findUnique({
        where: { userId },
      });
      ticketFilter.customerId = customer?.id;
    }

    const [
      totalTickets,
      openTickets,
      resolvedTickets,
      closedTickets,
      recentTickets,
    ] = await Promise.all([
      prisma.ticket.count({ where: ticketFilter }),
      prisma.ticket.count({
        where: { ...ticketFilter, status: 'Open' },
      }),
      prisma.ticket.count({
        where: { ...ticketFilter, status: 'Resolved' },
      }),
      prisma.ticket.count({
        where: { ...ticketFilter, status: 'Closed' },
      }),
      prisma.ticket.findMany({
        where: {
          ...ticketFilter,
          createdAt: { gte: thirtyDaysAgo },
        },
        orderBy: { createdAt: 'desc' },
        take: 10,
        include: {
          customer: { include: { user: true } },
          assignedTo: true,
        },
      }),
    ]);

    // Calculate average response/resolution times
    const ticketsWithTimes = await prisma.ticket.findMany({
      where: {
        ...ticketFilter,
        firstRespondedOn: { not: null },
      },
      select: {
        createdAt: true,
        firstRespondedOn: true,
        resolutionDate: true,
      },
    });

    let avgResponseTime = 0;
    let avgResolutionTime = 0;

    if (ticketsWithTimes.length > 0) {
      const responseTimes = ticketsWithTimes
        .filter((t) => t.firstRespondedOn)
        .map((t) => {
          const diff = t.firstRespondedOn!.getTime() - t.createdAt.getTime();
          return diff / (1000 * 60 * 60); // Convert to hours
        });

      const resolutionTimes = ticketsWithTimes
        .filter((t) => t.resolutionDate)
        .map((t) => {
          const diff = t.resolutionDate!.getTime() - t.createdAt.getTime();
          return diff / (1000 * 60 * 60); // Convert to hours
        });

      if (responseTimes.length > 0) {
        avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      }

      if (resolutionTimes.length > 0) {
        avgResolutionTime =
          resolutionTimes.reduce((a, b) => a + b, 0) / resolutionTimes.length;
      }
    }

    return {
      totalTickets,
      openTickets,
      resolvedTickets,
      closedTickets,
      avgResponseTime: Math.round(avgResponseTime * 10) / 10,
      avgResolutionTime: Math.round(avgResolutionTime * 10) / 10,
      recentTickets,
    };
  }
}

export const dashboardService = new DashboardService();
