import { Request, Response } from 'express';
import { prisma } from '../utils/prisma.js';
import { getFileUrl } from '../middleware/upload.js';
import { BadRequestError } from '../utils/errors.js';

export class UploadController {
  async uploadFile(req: Request, res: Response) {
    if (!req.file) {
      throw new BadRequestError('No file uploaded');
    }

    const file = req.file;
    const { ticketId, commentId } = req.body;

    // Create attachment record
    const attachment = await prisma.attachment.create({
      data: {
        fileName: file.originalname,
        fileUrl: getFileUrl(file.filename),
        fileSize: file.size,
        mimeType: file.mimetype,
        ticketId: ticketId || undefined,
        commentId: commentId || undefined,
        uploadedBy: req.user!.userId,
      },
    });

    res.status(201).json({
      status: 'success',
      data: { attachment },
    });
  }

  async uploadMultipleFiles(req: Request, res: Response) {
    if (!req.files || (req.files as Express.Multer.File[]).length === 0) {
      throw new BadRequestError('No files uploaded');
    }

    const files = req.files as Express.Multer.File[];
    const { ticketId, commentId } = req.body;

    // Create attachment records for all files
    const attachments = await Promise.all(
      files.map((file) =>
        prisma.attachment.create({
          data: {
            fileName: file.originalname,
            fileUrl: getFileUrl(file.filename),
            fileSize: file.size,
            mimeType: file.mimetype,
            ticketId: ticketId || undefined,
            commentId: commentId || undefined,
            uploadedBy: req.user!.userId,
          },
        })
      )
    );

    res.status(201).json({
      status: 'success',
      data: { attachments },
    });
  }

  async deleteFile(req: Request, res: Response) {
    const { id } = req.params;

    const attachment = await prisma.attachment.findUnique({
      where: { id },
    });

    if (!attachment) {
      throw new BadRequestError('Attachment not found');
    }

    // Check permissions (only uploader or admin can delete)
    if (
      attachment.uploadedBy !== req.user!.userId &&
      req.user!.userType !== 'ADMIN'
    ) {
      throw new BadRequestError('You do not have permission to delete this file');
    }

    await prisma.attachment.delete({
      where: { id },
    });

    res.json({
      status: 'success',
      message: 'File deleted successfully',
    });
  }
}

export const uploadController = new UploadController();
