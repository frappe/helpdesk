import { create } from 'zustand';
import { call } from '@/lib/api';
import { User } from '@/types';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  fetchUser: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  fetchUser: async () => {
    try {
      set({ isLoading: true });
      const user = await call<User>('helpdesk.api.auth.get_user');
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  logout: async () => {
    try {
      await call('logout');
      set({ user: null, isAuthenticated: false });
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  },
}));
