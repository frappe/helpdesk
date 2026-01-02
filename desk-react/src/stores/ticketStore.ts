import { create } from 'zustand';
import { getList, getDoc, createDoc, updateDoc } from '@/lib/api';
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
      const { data, total_count } = await getList<Ticket>('HD Ticket', {
        fields: ['*'],
        filters: options.filters || get().filters,
        limit_page_length: options.limit || 20,
        limit_start: options.offset || 0,
        order_by: 'modified desc',
      });
      set({ tickets: data, totalCount: total_count, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch tickets:', error);
      set({ isLoading: false });
    }
  },

  fetchTicket: async (id: string) => {
    try {
      set({ isLoading: true });
      const ticket = await getDoc<Ticket>('HD Ticket', id);
      set({ currentTicket: ticket, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch ticket:', error);
      set({ isLoading: false });
    }
  },

  createTicket: async (data: Partial<Ticket>) => {
    const ticket = await createDoc<Ticket>('HD Ticket', data);
    return ticket;
  },

  updateTicket: async (id: string, data: Partial<Ticket>) => {
    const ticket = await updateDoc<Ticket>('HD Ticket', id, data);
    set({ currentTicket: ticket });
    return ticket;
  },

  setFilters: (filters: Record<string, unknown>) => {
    set({ filters });
  },
}));
