import { create } from 'zustand';
import { login as apiLogin, logout as apiLogout, getCurrentUser } from '@/lib/api';
import { User } from '@/types';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  fetchUser: () => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    try {
      set({ isLoading: true });
      const user = await apiLogin(email, password);
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      throw error;
    }
  },

  fetchUser: async () => {
    try {
      set({ isLoading: true });
      const user = await getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  logout: async () => {
    try {
      await apiLogout();
      set({ user: null, isAuthenticated: false });
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
      // Clear state anyway
      set({ user: null, isAuthenticated: false });
      window.location.href = '/login';
    }
  },

  setUser: (user: User | null) => {
    set({ user, isAuthenticated: !!user });
  },
}));
