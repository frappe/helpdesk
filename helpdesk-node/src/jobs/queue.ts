import Bull from 'bull';
import { config } from '../config/index.js';
import { logger } from '../utils/logger.js';

// Create queues
export const emailQueue = new Bull('email-queue', {
  redis: {
    host: config.redis.host,
    port: config.redis.port,
    password: config.redis.password,
  },
});

export const slaQueue = new Bull('sla-queue', {
  redis: {
    host: config.redis.host,
    port: config.redis.port,
    password: config.redis.password,
  },
});

// Queue event listeners
emailQueue.on('completed', (job) => {
  logger.info(`Email job ${job.id} completed`);
});

emailQueue.on('failed', (job, err) => {
  logger.error(`Email job ${job?.id} failed:`, err);
});

slaQueue.on('completed', (job) => {
  logger.info(`SLA job ${job.id} completed`);
});

slaQueue.on('failed', (job, err) => {
  logger.error(`SLA job ${job?.id} failed:`, err);
});

logger.info('📋 Job queues initialized');
