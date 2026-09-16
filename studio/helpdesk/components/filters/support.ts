// Ported, not imported: the Studio build resolves only vue/vue-router/pinia/frappe-ui/
// reka-ui/@tiptap for files outside its project, so `@vueuse/core` cannot be reached.

import { getCurrentScope, onScopeDispose } from "vue";

// Bound for the life of the calling scope.
export function useEventListener(
  target: EventTarget,
  event: string,
  handler: EventListenerOrEventListenerObject,
  options?: AddEventListenerOptions,
) {
  target.addEventListener(event, handler, options);
  const stop = () => target.removeEventListener(event, handler, options);
  if (getCurrentScope()) onScopeDispose(stop);
  return stop;
}

export { debounce as useDebounceFn } from "frappe-ui";

// The desk spells it `__`.
export { t as __ } from '@app/stores/translations'

export function useDevice() {
  return { isMac: /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent) };
}

interface ShortcutBinding {
  key: string;
  shift?: boolean;
  ctrl?: boolean;
  alt?: boolean;
  meta?: boolean;
}

// No global registry: nothing in this portal lists its shortcuts.
export function useShortcut(binding: string | ShortcutBinding, callback: () => void) {
  const shortcut = normalize(binding);

  useEventListener(document, "keydown", (event: KeyboardEvent) => {
    if (typing()) return;
    if (event.key?.toLowerCase() !== shortcut.key.toLowerCase()) return;
    if (event.shiftKey !== Boolean(shortcut.shift)) return;
    if (event.altKey !== Boolean(shortcut.alt)) return;
    if (event.ctrlKey !== Boolean(shortcut.ctrl)) return;
    if (event.metaKey !== Boolean(shortcut.meta)) return;
    event.preventDefault();
    callback();
  });
}

// `meta` means Cmd on a Mac and Ctrl everywhere else.
function normalize(binding: string | ShortcutBinding): ShortcutBinding {
  const parsed: ShortcutBinding =
    typeof binding === "string" ? { key: binding } : { ...binding };
  if (parsed.meta && !useDevice().isMac) {
    parsed.ctrl = true;
    parsed.meta = false;
  }
  return parsed;
}

function typing(): boolean {
  const active = document.activeElement as HTMLElement | null;
  return Boolean(
    active instanceof HTMLInputElement ||
      active instanceof HTMLTextAreaElement ||
      active?.isContentEditable
  );
}
