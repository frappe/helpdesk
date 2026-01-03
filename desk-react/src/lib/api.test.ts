import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock axios before importing api
vi.mock('axios', () => {
  const mockAxios = {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: {
        use: vi.fn(),
      },
      response: {
        use: vi.fn(),
      },
    },
  };

  return {
    default: {
      create: vi.fn(() => mockAxios),
      ...mockAxios,
    },
  };
});

describe('API Utils', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
  });

  describe('call', () => {
    it('should make RPC call and return message', async () => {
      const axios = (await import('axios')).default;
      const mockAxiosInstance = axios.create();
      const mockData = { data: { message: { id: '1', name: 'Test' } } };

      vi.mocked(mockAxiosInstance.post).mockResolvedValue(mockData);

      const { call } = await import('./api');
      const result = await call('test.method', { arg1: 'value1' });

      expect(result).toEqual({ id: '1', name: 'Test' });
    });
  });

  describe('getDoc', () => {
    it('should fetch a single document', async () => {
      const axios = (await import('axios')).default;
      const mockAxiosInstance = axios.create();
      const mockData = { data: { data: { id: '1', name: 'Test Doc' } } };

      vi.mocked(mockAxiosInstance.get).mockResolvedValue(mockData);

      const { getDoc } = await import('./api');
      const result = await getDoc('Ticket', '1');

      expect(result).toEqual({ id: '1', name: 'Test Doc' });
    });
  });

  describe('getList', () => {
    it('should fetch list of documents', async () => {
      const axios = (await import('axios')).default;
      const mockAxiosInstance = axios.create();
      const mockData = {
        data: {
          data: [
            { id: '1', name: 'Doc 1' },
            { id: '2', name: 'Doc 2' },
          ],
          total_count: 2,
        },
      };

      vi.mocked(mockAxiosInstance.get).mockResolvedValue(mockData);

      const { getList } = await import('./api');
      const result = await getList('Ticket');

      expect(result.data).toHaveLength(2);
      expect(result.total_count).toBe(2);
    });

    it('should include filters and options in request', async () => {
      const axios = (await import('axios')).default;
      const mockAxiosInstance = axios.create();
      const mockData = { data: { data: [], total_count: 0 } };

      vi.mocked(mockAxiosInstance.get).mockResolvedValue(mockData);

      const { getList } = await import('./api');
      await getList('Ticket', {
        fields: ['name', 'subject'],
        filters: { status: 'Open' },
        limit_page_length: 10,
      });

      expect(mockAxiosInstance.get).toHaveBeenCalled();
    });
  });

  describe('createDoc', () => {
    it('should create a new document', async () => {
      const axios = (await import('axios')).default;
      const mockAxiosInstance = axios.create();
      const mockData = { data: { data: { id: '1', name: 'New Doc' } } };

      vi.mocked(mockAxiosInstance.post).mockResolvedValue(mockData);

      const { createDoc } = await import('./api');
      const result = await createDoc('Ticket', { name: 'New Doc' });

      expect(result).toEqual({ id: '1', name: 'New Doc' });
    });
  });

  describe('updateDoc', () => {
    it('should update an existing document', async () => {
      const axios = (await import('axios')).default;
      const mockAxiosInstance = axios.create();
      const mockData = { data: { data: { id: '1', name: 'Updated Doc' } } };

      vi.mocked(mockAxiosInstance.put).mockResolvedValue(mockData);

      const { updateDoc } = await import('./api');
      const result = await updateDoc('Ticket', '1', { name: 'Updated Doc' });

      expect(result).toEqual({ id: '1', name: 'Updated Doc' });
    });
  });

  describe('deleteDoc', () => {
    it('should delete a document', async () => {
      const axios = (await import('axios')).default;
      const mockAxiosInstance = axios.create();

      vi.mocked(mockAxiosInstance.delete).mockResolvedValue({});

      const { deleteDoc } = await import('./api');
      await expect(deleteDoc('Ticket', '1')).resolves.toBeUndefined();
    });
  });
});
