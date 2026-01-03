import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTicketStore } from './ticketStore';
import * as api from '@/lib/api';

vi.mock('@/lib/api');

describe('TicketStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    useTicketStore.setState({
      tickets: [],
      currentTicket: null,
      isLoading: false,
      totalCount: 0,
      filters: {},
    });
  });

  describe('fetchTickets', () => {
    it('should fetch tickets successfully', async () => {
      const mockTickets = [
        { id: '1', subject: 'Ticket 1', status: 'Open' },
        { id: '2', subject: 'Ticket 2', status: 'Closed' },
      ];

      vi.mocked(api.getList).mockResolvedValue({
        data: mockTickets,
        total_count: 2,
      });

      const { fetchTickets } = useTicketStore.getState();
      await fetchTickets();

      const state = useTicketStore.getState();
      expect(state.tickets).toEqual(mockTickets);
      expect(state.totalCount).toBe(2);
      expect(state.isLoading).toBe(false);
    });

    it('should handle fetch tickets error', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(api.getList).mockRejectedValue(new Error('Network error'));

      const { fetchTickets } = useTicketStore.getState();
      await fetchTickets();

      const state = useTicketStore.getState();
      expect(state.tickets).toEqual([]);
      expect(state.isLoading).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });

    it('should use provided filters and options', async () => {
      vi.mocked(api.getList).mockResolvedValue({ data: [], total_count: 0 });

      const { fetchTickets } = useTicketStore.getState();
      await fetchTickets({
        filters: { status: 'Open' },
        limit: 10,
        offset: 5,
      });

      expect(api.getList).toHaveBeenCalledWith('HD Ticket', {
        fields: ['*'],
        filters: { status: 'Open' },
        limit_page_length: 10,
        limit_start: 5,
        order_by: 'modified desc',
      });
    });

    it('should use store filters when no filters provided', async () => {
      useTicketStore.setState({ filters: { priority: 'High' } });
      vi.mocked(api.getList).mockResolvedValue({ data: [], total_count: 0 });

      const { fetchTickets } = useTicketStore.getState();
      await fetchTickets();

      expect(api.getList).toHaveBeenCalledWith('HD Ticket', expect.objectContaining({
        filters: { priority: 'High' },
      }));
    });
  });

  describe('fetchTicket', () => {
    it('should fetch single ticket successfully', async () => {
      const mockTicket = { id: '1', subject: 'Test Ticket', status: 'Open' };
      vi.mocked(api.getDoc).mockResolvedValue(mockTicket);

      const { fetchTicket } = useTicketStore.getState();
      await fetchTicket('1');

      const state = useTicketStore.getState();
      expect(state.currentTicket).toEqual(mockTicket);
      expect(state.isLoading).toBe(false);
    });

    it('should handle fetch ticket error', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(api.getDoc).mockRejectedValue(new Error('Not found'));

      const { fetchTicket } = useTicketStore.getState();
      await fetchTicket('999');

      const state = useTicketStore.getState();
      expect(state.currentTicket).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });
  });

  describe('createTicket', () => {
    it('should create ticket successfully', async () => {
      const newTicket = { subject: 'New Ticket', description: 'Test' };
      const createdTicket = { id: '3', ...newTicket, status: 'Open' };

      vi.mocked(api.createDoc).mockResolvedValue(createdTicket);

      const { createTicket } = useTicketStore.getState();
      const result = await createTicket(newTicket);

      expect(result).toEqual(createdTicket);
      expect(api.createDoc).toHaveBeenCalledWith('HD Ticket', newTicket);
    });
  });

  describe('updateTicket', () => {
    it('should update ticket successfully', async () => {
      const updates = { status: 'Closed' };
      const updatedTicket = { id: '1', subject: 'Test', status: 'Closed' };

      vi.mocked(api.updateDoc).mockResolvedValue(updatedTicket);

      const { updateTicket } = useTicketStore.getState();
      const result = await updateTicket('1', updates);

      expect(result).toEqual(updatedTicket);
      expect(useTicketStore.getState().currentTicket).toEqual(updatedTicket);
      expect(api.updateDoc).toHaveBeenCalledWith('HD Ticket', '1', updates);
    });
  });

  describe('setFilters', () => {
    it('should update filters', () => {
      const newFilters = { status: 'Open', priority: 'High' };

      const { setFilters } = useTicketStore.getState();
      setFilters(newFilters);

      expect(useTicketStore.getState().filters).toEqual(newFilters);
    });

    it('should replace existing filters', () => {
      useTicketStore.setState({ filters: { status: 'Open' } });

      const { setFilters } = useTicketStore.getState();
      setFilters({ priority: 'High' });

      expect(useTicketStore.getState().filters).toEqual({ priority: 'High' });
    });
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = useTicketStore.getState();

      expect(state.tickets).toEqual([]);
      expect(state.currentTicket).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.totalCount).toBe(0);
      expect(state.filters).toEqual({});
      expect(typeof state.fetchTickets).toBe('function');
      expect(typeof state.fetchTicket).toBe('function');
      expect(typeof state.createTicket).toBe('function');
      expect(typeof state.updateTicket).toBe('function');
      expect(typeof state.setFilters).toBe('function');
    });
  });
});
