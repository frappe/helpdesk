import { prisma } from '../setup.js';
import { createAgent } from './userFactory.js';
import { ArticleStatus } from '@prisma/client';

export const createCategory = async (overrides?: {
  name?: string;
  description?: string;
  parentId?: string;
}) => {
  const category = await prisma.category.create({
    data: {
      name: overrides?.name || `Category ${Date.now()}`,
      description: overrides?.description,
      parentId: overrides?.parentId,
    },
  });

  return category;
};

export const createArticle = async (overrides?: {
  title?: string;
  content?: string;
  categoryId?: string;
  authorId?: string;
  status?: ArticleStatus;
  isPublished?: boolean;
}) => {
  let categoryId = overrides?.categoryId;
  let authorId = overrides?.authorId;

  if (!categoryId) {
    const category = await createCategory();
    categoryId = category.id;
  }

  if (!authorId) {
    const { user } = await createAgent();
    authorId = user.id;
  }

  const article = await prisma.article.create({
    data: {
      title: overrides?.title || 'Test Article',
      content: overrides?.content || 'Test article content',
      categoryId,
      authorId,
      status: overrides?.status || 'PUBLISHED',
      isPublished: overrides?.isPublished !== undefined ? overrides.isPublished : true,
    },
    include: {
      category: true,
      author: true,
    },
  });

  return article;
};
