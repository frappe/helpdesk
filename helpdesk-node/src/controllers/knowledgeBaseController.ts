import { Request, Response } from 'express';
import { knowledgeBaseService } from '../services/knowledgeBaseService.js';
import { z } from 'zod';

const createArticleSchema = z.object({
  title: z.string().min(3),
  content: z.string().min(10),
  categoryId: z.string(),
  status: z.enum(['DRAFT', 'PUBLISHED']).optional(),
});

const updateArticleSchema = z.object({
  title: z.string().min(3).optional(),
  content: z.string().min(10).optional(),
  categoryId: z.string().optional(),
  status: z.enum(['DRAFT', 'PUBLISHED', 'ARCHIVED']).optional(),
});

const createCategorySchema = z.object({
  name: z.string().min(2),
  description: z.string().optional(),
  parentId: z.string().optional(),
});

export class KnowledgeBaseController {
  async createArticle(req: Request, res: Response) {
    const data = createArticleSchema.parse(req.body);
    const article = await knowledgeBaseService.createArticle({
      ...data,
      authorId: req.user!.userId,
    });

    res.status(201).json({
      status: 'success',
      data: { article },
    });
  }

  async listArticles(req: Request, res: Response) {
    const articles = await knowledgeBaseService.listArticles({
      categoryId: req.query.categoryId as string,
      status: req.query.status as string,
      search: req.query.search as string,
      isPublished:
        req.query.isPublished === 'true' ? true :
        req.query.isPublished === 'false' ? false : undefined,
    });

    res.json({
      status: 'success',
      data: { articles },
    });
  }

  async getArticle(req: Request, res: Response) {
    const { id } = req.params;
    const article = await knowledgeBaseService.getArticle(id);

    res.json({
      status: 'success',
      data: { article },
    });
  }

  async updateArticle(req: Request, res: Response) {
    const { id } = req.params;
    const data = updateArticleSchema.parse(req.body);
    const article = await knowledgeBaseService.updateArticle(id, data);

    res.json({
      status: 'success',
      data: { article },
    });
  }

  async deleteArticle(req: Request, res: Response) {
    const { id } = req.params;
    const result = await knowledgeBaseService.deleteArticle(id);

    res.json({
      status: 'success',
      ...result,
    });
  }

  async createCategory(req: Request, res: Response) {
    const data = createCategorySchema.parse(req.body);
    const category = await knowledgeBaseService.createCategory(
      data.name,
      data.description,
      data.parentId
    );

    res.status(201).json({
      status: 'success',
      data: { category },
    });
  }

  async listCategories(req: Request, res: Response) {
    const categories = await knowledgeBaseService.listCategories();

    res.json({
      status: 'success',
      data: { categories },
    });
  }

  async getCategory(req: Request, res: Response) {
    const { id } = req.params;
    const category = await knowledgeBaseService.getCategory(id);

    res.json({
      status: 'success',
      data: { category },
    });
  }
}

export const knowledgeBaseController = new KnowledgeBaseController();
