import { Router } from 'express';
import { knowledgeBaseController } from '../controllers/knowledgeBaseController.js';
import { authenticate, requireAgent } from '../middleware/auth.js';

const router = Router();

// Articles
router.post('/articles', authenticate, requireAgent, (req, res) =>
  knowledgeBaseController.createArticle(req, res)
);
router.get('/articles', (req, res) =>
  knowledgeBaseController.listArticles(req, res)
);
router.get('/articles/:id', (req, res) =>
  knowledgeBaseController.getArticle(req, res)
);
router.patch('/articles/:id', authenticate, requireAgent, (req, res) =>
  knowledgeBaseController.updateArticle(req, res)
);
router.delete('/articles/:id', authenticate, requireAgent, (req, res) =>
  knowledgeBaseController.deleteArticle(req, res)
);

// Categories
router.post('/categories', authenticate, requireAgent, (req, res) =>
  knowledgeBaseController.createCategory(req, res)
);
router.get('/categories', (req, res) =>
  knowledgeBaseController.listCategories(req, res)
);
router.get('/categories/:id', (req, res) =>
  knowledgeBaseController.getCategory(req, res)
);

export default router;
