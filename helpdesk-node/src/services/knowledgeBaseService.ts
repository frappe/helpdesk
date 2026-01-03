import { prisma } from '../utils/prisma.js';
import { NotFoundError } from '../utils/errors.js';

interface CreateArticleData {
  title: string;
  content: string;
  categoryId: string;
  authorId: string;
  status?: 'DRAFT' | 'PUBLISHED';
}

interface UpdateArticleData {
  title?: string;
  content?: string;
  categoryId?: string;
  status?: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
}

export class KnowledgeBaseService {
  async createArticle(data: CreateArticleData) {
    const article = await prisma.article.create({
      data: {
        title: data.title,
        content: data.content,
        categoryId: data.categoryId,
        authorId: data.authorId,
        status: data.status || 'DRAFT',
        isPublished: data.status === 'PUBLISHED',
      },
      include: {
        category: true,
        author: true,
      },
    });

    return article;
  }

  async listArticles(filters: {
    categoryId?: string;
    status?: string;
    search?: string;
    isPublished?: boolean;
  }) {
    const where: any = {};

    if (filters.categoryId) where.categoryId = filters.categoryId;
    if (filters.status) where.status = filters.status;
    if (filters.isPublished !== undefined) where.isPublished = filters.isPublished;

    if (filters.search) {
      where.OR = [
        { title: { contains: filters.search, mode: 'insensitive' } },
        { content: { contains: filters.search, mode: 'insensitive' } },
      ];
    }

    const articles = await prisma.article.findMany({
      where,
      include: {
        category: true,
        author: {
          select: {
            id: true,
            fullName: true,
            email: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    return articles;
  }

  async getArticle(id: string) {
    const article = await prisma.article.findUnique({
      where: { id },
      include: {
        category: true,
        author: {
          select: {
            id: true,
            fullName: true,
            email: true,
          },
        },
      },
    });

    if (!article) {
      throw new NotFoundError('Article not found');
    }

    // Increment view count
    await prisma.article.update({
      where: { id },
      data: { views: { increment: 1 } },
    });

    return article;
  }

  async updateArticle(id: string, data: UpdateArticleData) {
    const article = await prisma.article.update({
      where: { id },
      data: {
        ...data,
        isPublished: data.status === 'PUBLISHED',
      },
      include: {
        category: true,
        author: true,
      },
    });

    return article;
  }

  async deleteArticle(id: string) {
    await prisma.article.delete({
      where: { id },
    });

    return { message: 'Article deleted successfully' };
  }

  async createCategory(name: string, description?: string, parentId?: string) {
    const category = await prisma.category.create({
      data: {
        name,
        description,
        parentId,
      },
      include: {
        parent: true,
        _count: {
          select: { articles: true },
        },
      },
    });

    return category;
  }

  async listCategories() {
    const categories = await prisma.category.findMany({
      include: {
        parent: true,
        children: true,
        _count: {
          select: { articles: true },
        },
      },
      orderBy: { name: 'asc' },
    });

    return categories;
  }

  async getCategory(id: string) {
    const category = await prisma.category.findUnique({
      where: { id },
      include: {
        parent: true,
        children: true,
        articles: {
          where: { isPublished: true },
          include: {
            author: {
              select: {
                id: true,
                fullName: true,
              },
            },
          },
          orderBy: { createdAt: 'desc' },
        },
      },
    });

    if (!category) {
      throw new NotFoundError('Category not found');
    }

    return category;
  }
}

export const knowledgeBaseService = new KnowledgeBaseService();
