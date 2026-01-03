import bcrypt from 'bcryptjs';
import { prisma } from '../setup.js';
import { UserType } from '@prisma/client';

export const createUser = async (overrides?: {
  email?: string;
  password?: string;
  fullName?: string;
  userType?: UserType;
  isActive?: boolean;
}) => {
  const defaultData = {
    email: `test${Date.now()}@example.com`,
    password: 'password123',
    fullName: 'Test User',
    userType: 'CUSTOMER' as UserType,
    isActive: true,
  };

  const data = { ...defaultData, ...overrides };
  const hashedPassword = await bcrypt.hash(data.password, 10);

  const user = await prisma.user.create({
    data: {
      email: data.email,
      password: hashedPassword,
      fullName: data.fullName,
      userType: data.userType,
      isActive: data.isActive,
    },
  });

  return { user, password: data.password };
};

export const createAgent = async (overrides?: { email?: string; password?: string; agentName?: string }) => {
  const { user, password } = await createUser({
    userType: 'AGENT',
    ...(overrides?.email && { email: overrides.email }),
    ...(overrides?.password && { password: overrides.password }),
    fullName: overrides?.agentName || 'Test Agent',
  });

  const agent = await prisma.agent.create({
    data: {
      userId: user.id,
      agentName: user.fullName,
    },
  });

  return { user, agent, password };
};

export const createCustomer = async (overrides?: {
  email?: string;
  password?: string;
  customerName?: string;
}) => {
  const { user, password } = await createUser({
    userType: 'CUSTOMER',
    ...(overrides?.email && { email: overrides.email }),
    ...(overrides?.password && { password: overrides.password }),
    fullName: overrides?.customerName || 'Test Customer',
  });

  const customer = await prisma.customer.create({
    data: {
      userId: user.id,
      customerName: user.fullName,
    },
  });

  return { user, customer, password };
};

export const createAdmin = async () => {
  return await createUser({
    userType: 'ADMIN',
    fullName: 'Admin User',
  });
};
