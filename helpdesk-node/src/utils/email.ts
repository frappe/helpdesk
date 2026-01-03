import nodemailer from 'nodemailer';
import { config } from '../config/index.js';
import { logger } from './logger.js';

// Lazy-load transporter to avoid initialization in test environment
let transporter: nodemailer.Transporter | null = null;

const getTransporter = () => {
  if (!transporter && process.env.NODE_ENV !== 'test') {
    transporter = nodemailer.createTransport({
      host: config.email.smtp.host,
      port: config.email.smtp.port,
      secure: config.email.smtp.secure,
      auth: {
        user: config.email.smtp.auth.user,
        pass: config.email.smtp.auth.pass,
      },
    });

    // Verify transporter configuration
    transporter.verify((error) => {
      if (error) {
        logger.error('Email transporter error:', error);
      } else {
        logger.info('✉️  Email service ready');
      }
    });
  }
  return transporter;
};

interface EmailOptions {
  to: string;
  subject: string;
  html: string;
  text?: string;
}

export const sendEmail = async (options: EmailOptions) => {
  const emailTransporter = getTransporter();

  if (!emailTransporter) {
    logger.warn('Email transporter not initialized (test mode)');
    return { messageId: 'test-mode-no-email' };
  }

  try {
    const info = await emailTransporter.sendMail({
      from: config.email.from,
      to: options.to,
      subject: options.subject,
      html: options.html,
      text: options.text,
    });

    logger.info(`Email sent: ${info.messageId}`);
    return info;
  } catch (error) {
    logger.error('Failed to send email:', error);
    throw error;
  }
};

// Email Templates
export const emailTemplates = {
  ticketCreated: (data: {
    customerName: string;
    ticketId: string;
    subject: string;
    description: string;
  }) => ({
    subject: `New Ticket Created: ${data.subject}`,
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
            .content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-radius: 0 0 8px 8px; }
            .ticket-info { background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .label { font-weight: bold; color: #6b7280; }
            .value { color: #111827; margin-bottom: 10px; }
            .button { display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }
            .footer { text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>Ticket Confirmation</h1>
            </div>
            <div class="content">
              <p>Dear ${data.customerName},</p>
              <p>Thank you for contacting us. We have received your support request and created a ticket for you.</p>

              <div class="ticket-info">
                <div class="label">Ticket ID</div>
                <div class="value">#${data.ticketId}</div>

                <div class="label">Subject</div>
                <div class="value">${data.subject}</div>

                <div class="label">Description</div>
                <div class="value">${data.description || 'No description provided'}</div>
              </div>

              <p>Our support team will review your ticket and respond as soon as possible.</p>

              <a href="${process.env.APP_URL || 'http://localhost:8080'}/my-tickets/${data.ticketId}" class="button">View Ticket</a>

              <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; ${new Date().getFullYear()} Helpdesk. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
    text: `
Dear ${data.customerName},

Thank you for contacting us. We have received your support request.

Ticket ID: #${data.ticketId}
Subject: ${data.subject}
Description: ${data.description || 'No description provided'}

Our support team will review your ticket and respond as soon as possible.

View your ticket: ${process.env.APP_URL || 'http://localhost:8080'}/my-tickets/${data.ticketId}

This is an automated message. Please do not reply to this email.
    `,
  }),

  ticketAssigned: (data: {
    agentName: string;
    ticketId: string;
    subject: string;
    customerName: string;
    priority: string;
  }) => ({
    subject: `Ticket Assigned: ${data.subject}`,
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
            .content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-radius: 0 0 8px 8px; }
            .ticket-info { background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .label { font-weight: bold; color: #6b7280; }
            .value { color: #111827; margin-bottom: 10px; }
            .priority { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .priority-high { background-color: #fee2e2; color: #dc2626; }
            .priority-medium { background-color: #fef3c7; color: #d97706; }
            .priority-low { background-color: #dbeafe; color: #2563eb; }
            .button { display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }
            .footer { text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>New Ticket Assignment</h1>
            </div>
            <div class="content">
              <p>Hi ${data.agentName},</p>
              <p>A new ticket has been assigned to you.</p>

              <div class="ticket-info">
                <div class="label">Ticket ID</div>
                <div class="value">#${data.ticketId}</div>

                <div class="label">Subject</div>
                <div class="value">${data.subject}</div>

                <div class="label">Customer</div>
                <div class="value">${data.customerName}</div>

                <div class="label">Priority</div>
                <div class="value">
                  <span class="priority priority-${data.priority.toLowerCase()}">${data.priority}</span>
                </div>
              </div>

              <p>Please review and respond to this ticket at your earliest convenience.</p>

              <a href="${process.env.APP_URL || 'http://localhost:8080'}/tickets/${data.ticketId}" class="button">View Ticket</a>

              <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; ${new Date().getFullYear()} Helpdesk. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
    text: `
Hi ${data.agentName},

A new ticket has been assigned to you.

Ticket ID: #${data.ticketId}
Subject: ${data.subject}
Customer: ${data.customerName}
Priority: ${data.priority}

Please review and respond to this ticket at your earliest convenience.

View ticket: ${process.env.APP_URL || 'http://localhost:8080'}/tickets/${data.ticketId}
    `,
  }),

  ticketStatusUpdated: (data: {
    customerName: string;
    ticketId: string;
    subject: string;
    oldStatus: string;
    newStatus: string;
  }) => ({
    subject: `Ticket ${data.newStatus}: ${data.subject}`,
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
            .content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-radius: 0 0 8px 8px; }
            .ticket-info { background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .label { font-weight: bold; color: #6b7280; }
            .value { color: #111827; margin-bottom: 10px; }
            .status { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .status-resolved { background-color: #d1fae5; color: #065f46; }
            .button { display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }
            .footer { text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>Ticket Status Updated</h1>
            </div>
            <div class="content">
              <p>Dear ${data.customerName},</p>
              <p>The status of your support ticket has been updated.</p>

              <div class="ticket-info">
                <div class="label">Ticket ID</div>
                <div class="value">#${data.ticketId}</div>

                <div class="label">Subject</div>
                <div class="value">${data.subject}</div>

                <div class="label">Status Change</div>
                <div class="value">${data.oldStatus} → <span class="status status-resolved">${data.newStatus}</span></div>
              </div>

              <a href="${process.env.APP_URL || 'http://localhost:8080'}/my-tickets/${data.ticketId}" class="button">View Ticket</a>

              <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; ${new Date().getFullYear()} Helpdesk. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
    text: `
Dear ${data.customerName},

The status of your support ticket has been updated.

Ticket ID: #${data.ticketId}
Subject: ${data.subject}
Status: ${data.oldStatus} → ${data.newStatus}

View your ticket: ${process.env.APP_URL || 'http://localhost:8080'}/my-tickets/${data.ticketId}
    `,
  }),

  commentAdded: (data: {
    recipientName: string;
    ticketId: string;
    subject: string;
    commenterName: string;
    commentText: string;
  }) => ({
    subject: `New Comment on: ${data.subject}`,
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
            .content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-radius: 0 0 8px 8px; }
            .comment-box { background-color: white; padding: 20px; border-left: 4px solid #3b82f6; margin: 20px 0; }
            .button { display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }
            .footer { text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>New Comment</h1>
            </div>
            <div class="content">
              <p>Hi ${data.recipientName},</p>
              <p>${data.commenterName} added a comment to ticket #${data.ticketId}:</p>

              <div class="comment-box">
                <p><strong>${data.commenterName}</strong></p>
                <p>${data.commentText}</p>
              </div>

              <a href="${process.env.APP_URL || 'http://localhost:8080'}/tickets/${data.ticketId}" class="button">View Ticket</a>

              <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; ${new Date().getFullYear()} Helpdesk. All rights reserved.</p>
              </div>
            </div>
          </div>
        </body>
      </html>
    `,
    text: `
Hi ${data.recipientName},

${data.commenterName} added a comment to ticket #${data.ticketId}:

"${data.commentText}"

View ticket: ${process.env.APP_URL || 'http://localhost:8080'}/tickets/${data.ticketId}
    `,
  }),
};
