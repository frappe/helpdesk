import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuthStore } from './authStore';
import * as api from '@/lib/api';

vi.mock('@/lib/api');

describe('AuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    useAuthStore.setState({
      user: null,
      isLoading: true,
      isAuthenticated: false,
    });
  });

  describe('fetchUser', () => {
    it('should fetch user successfully', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        fullName: 'Test User',
        userType: 'CUSTOMER' as const,
      };

      vi.mocked(api.call).mockResolvedValue(mockUser);

      const { fetchUser } = useAuthStore.getState();
      await fetchUser();

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
    });

    it('should handle fetch user error', async () => {
      vi.mocked(api.call).mockRejectedValue(new Error('Unauthorized'));

      const { fetchUser } = useAuthStore.getState();
      await fetchUser();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
    });

    it('should set loading state during fetch', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      vi.mocked(api.call).mockReturnValue(promise);

      const { fetchUser } = useAuthStore.getState();
      const fetchPromise = fetchUser();

      // Check loading state before resolution
      expect(useAuthStore.getState().isLoading).toBe(true);

      resolvePromise!({ id: '1', email: 'test@example.com' });
      await fetchPromise;

      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      // Set up initial authenticated state
      useAuthStore.setState({
        user: { id: '1', email: 'test@example.com', fullName: 'Test User', userType: 'CUSTOMER' },
        isAuthenticated: true,
        isLoading: false,
      });

      vi.mocked(api.call).mockResolvedValue(undefined);
      delete (window as any).location;
      (window as any).location = { href: '' };

      const { logout } = useAuthStore.getState();
      await logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(window.location.href).toBe('/login');
    });

    it('should handle logout error', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(api.call).mockRejectedValue(new Error('Logout failed'));

      const { logout } = useAuthStore.getState();
      await logout();

      expect(consoleErrorSpy).toHaveBeenCalledWith('Logout failed:', expect.any(Error));
      consoleErrorSpy.mockRestore();
    });
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      // Create a fresh store instance
      const state = useAuthStore.getState();

      expect(state.user).toBeNull();
      expect(state.isLoading).toBe(true);
      expect(state.isAuthenticated).toBe(false);
      expect(typeof state.fetchUser).toBe('function');
      expect(typeof state.logout).toBe('function');
    });
  });
});
