// The desk utilities the ported filter leans on, in the smallest form this app needs.
//
// Ported rather than imported for two reasons: `@/` resolves inside the desk SPA only, and
// the Studio build re-resolves just `vue`, `vue-router`, `pinia`, `frappe-ui`, `reka-ui`
// and `@tiptap` for files outside its own project — so `@vueuse/core`, which the desk
// versions use, cannot be reached from here at all.

import { getCurrentScope, onScopeDispose } from "vue";

/** `@vueuse/core`'s, in the form this port uses: bind for the life of the calling scope. */
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

/** `@vueuse/core`'s `useDebounceFn`: the trailing call wins, the rest are dropped. */
export function useDebounceFn<T extends (...args: any[]) => void>(fn: T, wait: number) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

/** The portal ships no translations, so this is the identity the desk's `__` collapses to
 *  here. Kept as a call rather than removed, so a future i18n pass has one place to fill. */
export function __(text: string): string {
  return text;
}

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

/**
 * A single keyboard shortcut, ignored while the reader is typing.
 *
 * The desk keeps a global registry so its shortcut sheet can list every binding; nothing
 * in this portal lists them, so the registry goes and this is just the listener.
 */
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

/** `meta` means Cmd on a Mac and Ctrl everywhere else, as the desk's parser resolves it. */
function normalize(binding: string | ShortcutBinding): ShortcutBinding {
  const parsed: ShortcutBinding =
    typeof binding === "string" ? { key: binding } : { ...binding };
  if (parsed.meta && !useDevice().isMac) {
    parsed.ctrl = true;
    parsed.meta = false;
  }
  return parsed;
}

/** A shortcut must never steal a keystroke meant for a field. */
function typing(): boolean {
  const active = document.activeElement as HTMLElement | null;
  return Boolean(
    active instanceof HTMLInputElement ||
      active instanceof HTMLTextAreaElement ||
      active?.isContentEditable
  );
}
