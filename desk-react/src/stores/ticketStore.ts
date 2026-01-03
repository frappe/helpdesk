import { create } from 'zustand';
import { getTickets, getTicket, createTicket as apiCreateTicket, updateTicket as apiUpdateTicket } from '@/lib/api';
import { Ticket } from '@/types';

interface TicketState {
  tickets: Ticket[];
  currentTicket: Ticket | null;
  isLoading: boolean;
  totalCount: number;
  filters: Record<string, unknown>;

  fetchTickets: (options?: {
    filters?: Record<string, unknown>;
    limit?: number;
    offset?: number;
  }) => Promise<void>;

  fetchTicket: (id: string) => Promise<void>;
  createTicket: (data: Partial<Ticket>) => Promise<Ticket>;
  updateTicket: (id: string, data: Partial<Ticket>) => Promise<Ticket>;
  setFilters: (filters: Record<string, unknown>) => void;
}

export const useTicketStore = create<TicketState>((set, get) => ({
  tickets: [],
  currentTicket: null,
  isLoading: false,
  totalCount: 0,
  filters: {},

  fetchTickets: async (options = {}) => {
    try {
      set({ isLoading: true });
      const response = await getTickets({
        ...options.filters,
        ...get().filters,
        limit: options.limit || 20,
        offset: options.offset || 0,
      });

      // Handle both array and paginated response
      const tickets = Array.isArray(response) ? response : response.data || response;
      const totalCount = Array.isArray(response) ? response.length : response.totalCount || response.length;

      set({ tickets, totalCount, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch tickets:', error);
      set({ isLoading: false });
    }
  },

  fetchTicket: async (id: string) => {
    try {
      set({ isLoading: true });
      const ticket = await getTicket(id);
      set({ currentTicket: ticket, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch ticket:', error);
      set({ isLoading: false });
    }
  },

  createTicket: async (data: Partial<Ticket>) => {
    const ticket = await apiCreateTicket(data as any);
    return ticket;
  },

  updateTicket: async (id: string, data: Partial<Ticket>) => {
    const ticket = await apiUpdateTicket(id, data);
    set({ currentTicket: ticket });
    return ticket;
  },

  setFilters: (filters: Record<string, unknown>) => {
    set({ filters });
  },
}));
