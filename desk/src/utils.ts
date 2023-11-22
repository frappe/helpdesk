import { useClipboard } from '@vueuse/core';
import { call, toast } from 'frappe-ui';

/**
 * Wrapper to create toasts, supplied with default options.
 * https://frappeui.com/components/toast.html
 * @param options - `Toast` options
 */
export function createToast(options?: Record<string, string>) {
  toast({
    position: 'bottom-right',
    ...options,
  });
}

/**
 * Copy a string to clipboard, and create a toast
 * @param s - String to copy
 */
export async function copy(s: string) {
  const { copy: c } = useClipboard();
  c(s).then(() =>
    createToast({
      title: 'Copied to clipboard',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  );
}

/**
 * Get assigned user from `_assign` string. The return value is a `string`,
 * not a `User` object.
 * @param s - `_assign` string (JSON)
 * @returns user id
 */
export function getAssign(s: string): string | undefined {
  const assignJson = JSON.parse(s);
  const arr = Array.isArray(assignJson) ? assignJson : [];
  return arr.slice(-1).pop();
}

/**
 * Track visit to a document.
 * @param dt - DocType
 * @param dn - DocName
 */
export function trackVisit(dt: string, dn: string) {
  return call('helpdesk.helpdesk.doctype.hd_visit.hd_visit.track_visit', {
    dt,
    dn,
  });
}
