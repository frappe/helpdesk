import { describe, it, expect, beforeEach } from 'vitest';
import { KnowledgeBaseService } from '../../src/services/knowledgeBaseService.js';
import { createArticle, createCategory } from '../factories/articleFactory.js';
import { createAgent } from '../factories/userFactory.js';
import { NotFoundError } from '../../src/utils/errors.js';
import { prisma } from '../setup.js';

describe('KnowledgeBaseService', () => {
  let kbService: KnowledgeBaseService;

  beforeEach(() => {
    kbService = new KnowledgeBaseService();
  });

  describe('createArticle', () => {
    it('should create article successfully', async () => {
      const { user } = await createAgent();
      const category = await createCategory();

      const article = await kbService.createArticle({
        title: 'Test Article',
        content: 'Test content',
        categoryId: category.id,
        authorId: user.id,
        status: 'PUBLISHED',
      });

      expect(article).toBeDefined();
      expect(article.title).toBe('Test Article');
      expect(article.status).toBe('PUBLISHED');
      expect(article.isPublished).toBe(true);
    });

    it('should create draft article by default', async () => {
      const { user } = await createAgent();
      const category = await createCategory();

      const article = await kbService.createArticle({
        title: 'Draft Article',
        content: 'Draft content',
        categoryId: category.id,
        authorId: user.id,
      });

      expect(article.status).toBe('DRAFT');
      expect(article.isPublished).toBe(false);
    });
  });

  describe('listArticles', () => {
    it('should list all articles', async () => {
      await createArticle();
      await createArticle();
      await createArticle();

      const articles = await kbService.listArticles({});

      expect(articles.length).toBe(3);
    });

    it('should filter articles by category', async () => {
      const category1 = await createCategory({ name: 'Category 1' });
      const category2 = await createCategory({ name: 'Category 2' });

      await createArticle({ categoryId: category1.id });
      await createArticle({ categoryId: category1.id });
      await createArticle({ categoryId: category2.id });

      const articles = await kbService.listArticles({
        categoryId: category1.id,
      });

      expect(articles.length).toBe(2);
      expect(articles.every((a) => a.categoryId === category1.id)).toBe(true);
    });

    it('should filter articles by status', async () => {
      await createArticle({ status: 'PUBLISHED' });
      await createArticle({ status: 'DRAFT' });
      await createArticle({ status: 'PUBLISHED' });

      const articles = await kbService.listArticles({ status: 'PUBLISHED' });

      expect(articles.length).toBe(2);
      expect(articles.every((a) => a.status === 'PUBLISHED')).toBe(true);
    });

    it('should filter by isPublished flag', async () => {
      await createArticle({ isPublished: true });
      await createArticle({ isPublished: false });
      await createArticle({ isPublished: true });

      const articles = await kbService.listArticles({ isPublished: true });

      expect(articles.length).toBe(2);
    });

    it('should search articles by title', async () => {
      await createArticle({ title: 'How to Login' });
      await createArticle({ title: 'Payment Methods' });
      await createArticle({ title: 'Login Issues' });

      const articles = await kbService.listArticles({ search: 'login' });

      expect(articles.length).toBe(2);
    });
  });

  describe('getArticle', () => {
    it('should get article and increment views', async () => {
      const article = await createArticle();
      const initialViews = article.views;

      const result = await kbService.getArticle(article.id);

      expect(result).toBeDefined();
      expect(result.id).toBe(article.id);

      // Check views were incremented
      const updated = await prisma.article.findUnique({
        where: { id: article.id },
      });
      expect(updated?.views).toBe(initialViews + 1);
    });

    it('should throw NotFoundError for non-existent article', async () => {
      await expect(kbService.getArticle('non-existent-id')).rejects.toThrow(
        NotFoundError
      );
    });
  });

  describe('updateArticle', () => {
    it('should update article fields', async () => {
      const article = await createArticle({ status: 'DRAFT' });

      const updated = await kbService.updateArticle(article.id, {
        title: 'Updated Title',
        status: 'PUBLISHED',
      });

      expect(updated.title).toBe('Updated Title');
      expect(updated.status).toBe('PUBLISHED');
      expect(updated.isPublished).toBe(true);
    });
  });

  describe('deleteArticle', () => {
    it('should delete article successfully', async () => {
      const article = await createArticle();

      await kbService.deleteArticle(article.id);

      const deleted = await prisma.article.findUnique({
        where: { id: article.id },
      });

      expect(deleted).toBeNull();
    });
  });

  describe('createCategory', () => {
    it('should create category successfully', async () => {
      const category = await kbService.createCategory(
        'Test Category',
        'Test description'
      );

      expect(category).toBeDefined();
      expect(category.name).toBe('Test Category');
      expect(category.description).toBe('Test description');
    });

    it('should create subcategory with parent', async () => {
      const parent = await createCategory();

      const child = await kbService.createCategory(
        'Child Category',
        undefined,
        parent.id
      );

      expect(child.parentId).toBe(parent.id);
      expect(child.parent?.id).toBe(parent.id);
    });
  });

  describe('listCategories', () => {
    it('should list all categories', async () => {
      await createCategory();
      await createCategory();

      const categories = await kbService.listCategories();

      expect(categories.length).toBe(2);
    });

    it('should include article count', async () => {
      const category = await createCategory();
      await createArticle({ categoryId: category.id });
      await createArticle({ categoryId: category.id });

      const categories = await kbService.listCategories();
      const result = categories.find((c) => c.id === category.id);

      expect(result?._count.articles).toBe(2);
    });
  });

  describe('getCategory', () => {
    it('should get category with articles', async () => {
      const category = await createCategory();
      await createArticle({ categoryId: category.id, isPublished: true });
      await createArticle({ categoryId: category.id, isPublished: false });

      const result = await kbService.getCategory(category.id);

      expect(result).toBeDefined();
      expect(result.articles.length).toBe(1); // Only published
    });

    it('should throw NotFoundError for non-existent category', async () => {
      await expect(kbService.getCategory('non-existent-id')).rejects.toThrow(
        NotFoundError
      );
    });
  });
});
