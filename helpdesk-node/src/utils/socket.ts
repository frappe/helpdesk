import { Server as SocketIOServer } from 'socket.io';
import { Server as HTTPServer } from 'http';
import { verifyToken } from './jwt.js';
import { logger } from './logger.js';

let io: SocketIOServer;

export const initializeSocket = (server: HTTPServer) => {
  io = new SocketIOServer(server, {
    cors: {
      origin: process.env.CORS_ORIGIN || 'http://localhost:8080',
      credentials: true,
    },
  });

  // Authentication middleware
  io.use((socket, next) => {
    const token = socket.handshake.auth.token;

    if (!token) {
      return next(new Error('Authentication required'));
    }

    try {
      const payload = verifyToken(token);
      socket.data.user = payload;
      next();
    } catch (error) {
      next(new Error('Invalid token'));
    }
  });

  // Connection handler
  io.on('connection', (socket) => {
    const user = socket.data.user;
    logger.info(`User connected: ${user.email} (${socket.id})`);

    // Join user-specific room
    socket.join(`user:${user.userId}`);

    // Join role-specific room
    socket.join(`role:${user.userType}`);

    // Handle joining ticket rooms
    socket.on('join:ticket', (ticketId: string) => {
      socket.join(`ticket:${ticketId}`);
      logger.info(`User ${user.email} joined ticket room: ${ticketId}`);
    });

    socket.on('leave:ticket', (ticketId: string) => {
      socket.leave(`ticket:${ticketId}`);
      logger.info(`User ${user.email} left ticket room: ${ticketId}`);
    });

    // Typing indicators
    socket.on('typing:start', (ticketId: string) => {
      socket.to(`ticket:${ticketId}`).emit('user:typing', {
        userId: user.userId,
        userName: user.email,
        ticketId,
      });
    });

    socket.on('typing:stop', (ticketId: string) => {
      socket.to(`ticket:${ticketId}`).emit('user:stopped-typing', {
        userId: user.userId,
        ticketId,
      });
    });

    // Disconnect handler
    socket.on('disconnect', () => {
      logger.info(`User disconnected: ${user.email} (${socket.id})`);
    });
  });

  logger.info('Socket.io initialized');
  return io;
};

export const getIO = () => {
  if (!io) {
    throw new Error('Socket.io not initialized');
  }
  return io;
};

// Event emitters
export const emitTicketCreated = (ticket: any) => {
  io.to('role:AGENT').emit('ticket:created', ticket);
};

export const emitTicketUpdated = (ticketId: string, ticket: any) => {
  io.to(`ticket:${ticketId}`).emit('ticket:updated', ticket);
};

export const emitTicketAssigned = (ticketId: string, agentId: string, ticket: any) => {
  io.to(`user:${agentId}`).emit('ticket:assigned', ticket);
  io.to(`ticket:${ticketId}`).emit('ticket:updated', ticket);
};

export const emitCommentAdded = (ticketId: string, comment: any) => {
  io.to(`ticket:${ticketId}`).emit('comment:added', comment);
};

export const emitNotification = (userId: string, notification: any) => {
  io.to(`user:${userId}`).emit('notification:new', notification);
};
