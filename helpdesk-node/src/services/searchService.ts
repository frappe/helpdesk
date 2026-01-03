import { prisma } from '../utils/prisma.js';
import { Prisma } from '@prisma/client';

export class SearchService {
  async searchTickets(
    query: string,
    userId: string,
    userType: string,
    options?: {
      status?: string;
      priority?: string;
      limit?: number;
    }
  ) {
    const limit = options?.limit || 20;

    // Build base where clause
    const where: Prisma.TicketWhereInput = {
      AND: [
        {
          OR: [
            { subject: { contains: query, mode: 'insensitive' } },
            { description: { contains: query, mode: 'insensitive' } },
            { id: { contains: query, mode: 'insensitive' } },
          ],
        },
      ],
    };

    // Add filter conditions
    if (options?.status) {
      where.AND!.push({ status: options.status });
    }
    if (options?.priority) {
      where.AND!.push({ priority: options.priority as any });
    }

    // Role-based filtering
    if (userType === 'CUSTOMER') {
      const customer = await prisma.customer.findUnique({
        where: { userId },
      });
      if (customer) {
        where.AND!.push({ customerId: customer.id });
      }
    }

    const tickets = await prisma.ticket.findMany({
      where,
      include: {
        customer: {
          include: { user: true },
        },
        raisedBy: true,
        assignedTo: true,
        _count: {
          select: { comments: true },
        },
      },
      orderBy: [
        { updatedAt: 'desc' },
      ],
      take: limit,
    });

    return tickets;
  }

  async searchArticles(query: string, limit = 20) {
    const articles = await prisma.article.findMany({
      where: {
        isPublished: true,
        OR: [
          { title: { contains: query, mode: 'insensitive' } },
          { content: { contains: query, mode: 'insensitive' } },
        ],
      },
      include: {
        category: true,
        author: {
          select: {
            id: true,
            fullName: true,
          },
        },
      },
      orderBy: [
        { views: 'desc' },
        { updatedAt: 'desc' },
      ],
      take: limit,
    });

    // Increment views for all returned articles
    if (articles.length > 0) {
      await prisma.article.updateMany({
        where: {
          id: { in: articles.map(a => a.id) },
        },
        data: {
          views: { increment: 1 },
        },
      });
    }

    return articles;
  }

  async searchCustomers(query: string, limit = 20) {
    const customers = await prisma.customer.findMany({
      where: {
        OR: [
          { customerName: { contains: query, mode: 'insensitive' } },
          { user: { email: { contains: query, mode: 'insensitive' } } },
          { mobileNo: { contains: query } },
        ],
      },
      include: {
        user: {
          select: {
            id: true,
            email: true,
            fullName: true,
          },
        },
        _count: {
          select: { tickets: true },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
      take: limit,
    });

    return customers;
  }

  async globalSearch(query: string, userId: string, userType: string) {
    // Run searches in parallel
    const [tickets, articles, customers] = await Promise.all([
      this.searchTickets(query, userId, userType, { limit: 10 }),
      this.searchArticles(query, 10),
      userType === 'AGENT' || userType === 'ADMIN'
        ? this.searchCustomers(query, 10)
        : Promise.resolve([]),
    ]);

    return {
      tickets,
      articles,
      customers,
      total: tickets.length + articles.length + customers.length,
    };
  }
}

export const searchService = new SearchService();
