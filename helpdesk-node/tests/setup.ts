import { beforeAll, afterAll, afterEach } from 'vitest';
import { PrismaClient } from '@prisma/client';

// Test database instance
export const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL || 'postgresql://test:test@localhost:5432/helpdesk_test',
    },
  },
});

beforeAll(async () => {
  // Connect to test database
  await prisma.$connect();
});

afterEach(async () => {
  // Clean up database after each test in correct order (respecting foreign keys)
  const deleteOperations = [
    prisma.refreshToken.deleteMany(),
    prisma.notification.deleteMany(),
    prisma.activity.deleteMany(),
    prisma.comment.deleteMany(),
    prisma.ticket.deleteMany(),
    prisma.article.deleteMany(),
    prisma.category.deleteMany(),
    prisma.customer.deleteMany(),
    prisma.user.deleteMany(),
  ];

  await prisma.$transaction(deleteOperations);
});

afterAll(async () => {
  // Disconnect from database
  await prisma.$disconnect();
});
