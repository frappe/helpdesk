import bcrypt from 'bcryptjs';
import { prisma } from '../utils/prisma.js';
import { generateAccessToken, generateRefreshToken } from '../utils/jwt.js';
import { UnauthorizedError, ConflictError } from '../utils/errors.js';
import { addDays } from 'date-fns';

interface RegisterData {
  email: string;
  password: string;
  fullName: string;
  userType?: 'AGENT' | 'CUSTOMER';
}

interface LoginData {
  email: string;
  password: string;
}

export class AuthService {
  async register(data: RegisterData) {
    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { email: data.email },
    });

    if (existingUser) {
      throw new ConflictError('User with this email already exists');
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(data.password, 10);

    // Create user
    const user = await prisma.user.create({
      data: {
        email: data.email,
        password: hashedPassword,
        fullName: data.fullName,
        userType: data.userType || 'CUSTOMER',
      },
      select: {
        id: true,
        email: true,
        fullName: true,
        userType: true,
      },
    });

    // Create customer or agent profile
    if (user.userType === 'CUSTOMER') {
      await prisma.customer.create({
        data: {
          userId: user.id,
          customerName: user.fullName,
        },
      });
    } else if (user.userType === 'AGENT') {
      await prisma.agent.create({
        data: {
          userId: user.id,
          agentName: user.fullName,
        },
      });
    }

    // Generate tokens
    const accessToken = generateAccessToken({
      userId: user.id,
      email: user.email,
      userType: user.userType,
    });

    const refreshToken = generateRefreshToken({
      userId: user.id,
      email: user.email,
      userType: user.userType,
    });

    // Store refresh token
    await prisma.refreshToken.create({
      data: {
        token: refreshToken,
        userId: user.id,
        expiresAt: addDays(new Date(), 30),
      },
    });

    return {
      user,
      accessToken,
      refreshToken,
    };
  }

  async login(data: LoginData) {
    // Find user
    const user = await prisma.user.findUnique({
      where: { email: data.email },
    });

    if (!user) {
      throw new UnauthorizedError('Invalid credentials');
    }

    if (!user.isActive) {
      throw new UnauthorizedError('Account is inactive');
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(data.password, user.password);

    if (!isValidPassword) {
      throw new UnauthorizedError('Invalid credentials');
    }

    // Generate tokens
    const accessToken = generateAccessToken({
      userId: user.id,
      email: user.email,
      userType: user.userType,
    });

    const refreshToken = generateRefreshToken({
      userId: user.id,
      email: user.email,
      userType: user.userType,
    });

    // Store refresh token
    await prisma.refreshToken.create({
      data: {
        token: refreshToken,
        userId: user.id,
        expiresAt: addDays(new Date(), 30),
      },
    });

    return {
      user: {
        id: user.id,
        email: user.email,
        fullName: user.fullName,
        userType: user.userType,
      },
      accessToken,
      refreshToken,
    };
  }

  async getMe(userId: string) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        email: true,
        fullName: true,
        userType: true,
        userImage: true,
        agent: true,
        customer: true,
      },
    });

    if (!user) {
      throw new UnauthorizedError('User not found');
    }

    return user;
  }

  async logout(token: string) {
    await prisma.refreshToken.delete({
      where: { token },
    });
  }

  async logoutAll(userId: string) {
    await prisma.refreshToken.deleteMany({
      where: { userId },
    });
  }

  async refreshToken(token: string) {
    // Find and validate refresh token
    const storedToken = await prisma.refreshToken.findUnique({
      where: { token },
      include: { user: true },
    });

    if (!storedToken) {
      throw new UnauthorizedError('Invalid refresh token');
    }

    if (storedToken.expiresAt < new Date()) {
      throw new UnauthorizedError('Refresh token expired');
    }

    // Generate new tokens
    const accessToken = generateAccessToken({
      userId: storedToken.user.id,
      email: storedToken.user.email,
      userType: storedToken.user.userType,
    });

    const newRefreshToken = generateRefreshToken({
      userId: storedToken.user.id,
      email: storedToken.user.email,
      userType: storedToken.user.userType,
    });

    // Delete old refresh token and create new one
    await prisma.refreshToken.delete({
      where: { token },
    });

    await prisma.refreshToken.create({
      data: {
        token: newRefreshToken,
        userId: storedToken.user.id,
        expiresAt: addDays(new Date(), 30),
      },
    });

    return {
      accessToken,
      refreshToken: newRefreshToken,
    };
  }
}

export const authService = new AuthService();
