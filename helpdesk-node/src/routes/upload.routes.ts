import { Router } from 'express';
import { uploadController } from '../controllers/uploadController.js';
import { authenticate } from '../middleware/auth.js';
import { upload } from '../middleware/upload.js';

const router = Router();

// All upload routes require authentication
router.use(authenticate);

// Single file upload
router.post('/file', upload.single('file'), (req, res) =>
  uploadController.uploadFile(req, res)
);

// Multiple file upload
router.post('/files', upload.array('files', 10), (req, res) =>
  uploadController.uploadMultipleFiles(req, res)
);

// Delete file
router.delete('/:id', (req, res) => uploadController.deleteFile(req, res));

export default router;
