import { Request, Response } from 'express';
import { searchService } from '../services/searchService.js';
import { BadRequestError } from '../utils/errors.js';

export class SearchController {
  async globalSearch(req: Request, res: Response) {
    const { q } = req.query;

    if (!q || typeof q !== 'string') {
      throw new BadRequestError('Search query is required');
    }

    if (q.length < 2) {
      throw new BadRequestError('Search query must be at least 2 characters');
    }

    const results = await searchService.globalSearch(
      q,
      req.user!.userId,
      req.user!.userType
    );

    res.json({
      status: 'success',
      data: results,
    });
  }

  async searchTickets(req: Request, res: Response) {
    const { q, status, priority, limit } = req.query;

    if (!q || typeof q !== 'string') {
      throw new BadRequestError('Search query is required');
    }

    const tickets = await searchService.searchTickets(
      q,
      req.user!.userId,
      req.user!.userType,
      {
        status: status as string,
        priority: priority as string,
        limit: limit ? parseInt(limit as string) : undefined,
      }
    );

    res.json({
      status: 'success',
      data: { tickets },
    });
  }

  async searchArticles(req: Request, res: Response) {
    const { q, limit } = req.query;

    if (!q || typeof q !== 'string') {
      throw new BadRequestError('Search query is required');
    }

    const articles = await searchService.searchArticles(
      q,
      limit ? parseInt(limit as string) : undefined
    );

    res.json({
      status: 'success',
      data: { articles },
    });
  }

  async searchCustomers(req: Request, res: Response) {
    const { q, limit } = req.query;

    if (!q || typeof q !== 'string') {
      throw new BadRequestError('Search query is required');
    }

    const customers = await searchService.searchCustomers(
      q,
      limit ? parseInt(limit as string) : undefined
    );

    res.json({
      status: 'success',
      data: { customers },
    });
  }
}

export const searchController = new SearchController();
