import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { cn, formatDate, formatDateTime, formatRelativeTime, getInitials, truncate } from './utils';

describe('Utils', () => {
  describe('cn', () => {
    it('should merge class names correctly', () => {
      const result = cn('bg-red-500', 'text-white');
      expect(result).toContain('bg-red-500');
      expect(result).toContain('text-white');
    });

    it('should handle conditional classes', () => {
      const result = cn('base-class', false && 'hidden-class', 'visible-class');
      expect(result).toContain('base-class');
      expect(result).toContain('visible-class');
      expect(result).not.toContain('hidden-class');
    });

    it('should merge conflicting tailwind classes', () => {
      const result = cn('p-4', 'p-8');
      // twMerge should keep only the last padding class
      expect(result).toBe('p-8');
    });
  });

  describe('formatDate', () => {
    it('should format date string correctly', () => {
      const result = formatDate('2024-01-15');
      expect(result).toBe('Jan 15, 2024');
    });

    it('should format Date object correctly', () => {
      const date = new Date('2024-01-15');
      const result = formatDate(date);
      expect(result).toBe('Jan 15, 2024');
    });
  });

  describe('formatDateTime', () => {
    it('should format date and time correctly', () => {
      const result = formatDateTime('2024-01-15T14:30:00');
      expect(result).toMatch(/Jan 15, 2024/);
      expect(result).toMatch(/2:30 PM/);
    });

    it('should handle Date object', () => {
      const date = new Date('2024-01-15T14:30:00');
      const result = formatDateTime(date);
      expect(result).toMatch(/Jan 15, 2024/);
      expect(result).toMatch(/2:30 PM/);
    });
  });

  describe('formatRelativeTime', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should return "just now" for recent times', () => {
      const now = new Date('2024-01-15T12:00:00');
      vi.setSystemTime(now);

      const result = formatRelativeTime(new Date('2024-01-15T11:59:30'));
      expect(result).toBe('just now');
    });

    it('should return minutes ago', () => {
      const now = new Date('2024-01-15T12:00:00');
      vi.setSystemTime(now);

      const result = formatRelativeTime(new Date('2024-01-15T11:55:00'));
      expect(result).toBe('5m ago');
    });

    it('should return hours ago', () => {
      const now = new Date('2024-01-15T12:00:00');
      vi.setSystemTime(now);

      const result = formatRelativeTime(new Date('2024-01-15T09:00:00'));
      expect(result).toBe('3h ago');
    });

    it('should return days ago', () => {
      const now = new Date('2024-01-15T12:00:00');
      vi.setSystemTime(now);

      const result = formatRelativeTime(new Date('2024-01-13T12:00:00'));
      expect(result).toBe('2d ago');
    });

    it('should return formatted date for older times', () => {
      const now = new Date('2024-01-15T12:00:00');
      vi.setSystemTime(now);

      const result = formatRelativeTime(new Date('2024-01-01T12:00:00'));
      expect(result).toBe('Jan 1, 2024');
    });
  });

  describe('getInitials', () => {
    it('should get initials from full name', () => {
      expect(getInitials('John Doe')).toBe('JD');
    });

    it('should handle single name', () => {
      expect(getInitials('John')).toBe('J');
    });

    it('should handle three names', () => {
      expect(getInitials('John Michael Doe')).toBe('JM');
    });

    it('should return uppercase initials', () => {
      expect(getInitials('john doe')).toBe('JD');
    });

    it('should handle empty string', () => {
      expect(getInitials('')).toBe('');
    });
  });

  describe('truncate', () => {
    it('should truncate long strings', () => {
      const result = truncate('This is a very long string', 10);
      expect(result).toBe('This is a ...');
    });

    it('should not truncate short strings', () => {
      const result = truncate('Short', 10);
      expect(result).toBe('Short');
    });

    it('should handle exact length', () => {
      const result = truncate('Exactly10!', 10);
      expect(result).toBe('Exactly10!');
    });

    it('should handle empty string', () => {
      const result = truncate('', 10);
      expect(result).toBe('');
    });
  });
});
