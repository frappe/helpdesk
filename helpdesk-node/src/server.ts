import express from 'express';
import { createServer } from 'http';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import 'express-async-errors';
import { config } from './config/index.js';
import { logger } from './utils/logger.js';
import { errorHandler } from './middleware/errorHandler.js';
import { requestLogger } from './middleware/requestLogger.js';
import { initializeSocket } from './utils/socket.js';
import './jobs/emailWorker.js'; // Initialize email worker
import './jobs/slaWorker.js'; // Initialize SLA worker
import { scheduleSLAJobs } from './jobs/slaWorker.js';
import routes from './routes/index.js';

const app = express();
const httpServer = createServer(app);

// Initialize Socket.io
initializeSocket(httpServer);

// Schedule background jobs
scheduleSLAJobs();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: config.cors.origin,
  credentials: true,
}));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Compression
app.use(compression());

// Request logging
app.use(requestLogger);

// Serve uploaded files
app.use('/uploads', express.static(config.upload.uploadDir));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API routes
app.use(config.api.prefix, routes);

// Error handling
app.use(errorHandler);

// Start server
const PORT = config.server.port;

httpServer.listen(PORT, () => {
  logger.info(`🚀 Server running on port ${PORT} in ${config.server.env} mode`);
  logger.info(`📡 API available at http://localhost:${PORT}${config.api.prefix}`);
  logger.info(`🔌 Socket.io ready for real-time connections`);
  logger.info(`📋 Background jobs and workers running`);
});

export default app;
