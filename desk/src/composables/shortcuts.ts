import { showCommentBox, showEmailBox } from "@/pages/ticket/modalStates";
import { computed, ref } from "vue";
import { useEventListener } from "@vueuse/core";
import { useDevice } from "@/composables";

interface ShortcutBinding {
  key: string;
  shift?: boolean;
  ctrl?: boolean;
  alt?: boolean;
  meta?: boolean; // Cmd on Mac
}

export const shortcutsList = ref<ShortcutBinding[]>([]);

export const useShortcut = (
  binding: string | ShortcutBinding,
  cb: Function
) => {
  const shortcutBinding = parseBinding(binding);

  registerShortcut(shortcutBinding);

  const handleKeydown = (e: KeyboardEvent) => {
    if (!isEventRegistered(e, shortcutBinding)) {
      return;
    }

    if (disableShortcuts()) {
      return; // Don't trigger shortcuts when typing, or in modals/menus
    }

    if (executeHandler(e, shortcutBinding)) {
      e.preventDefault();
      try {
        cb();
      } catch (error) {
        console.error("Error executing shortcut:", binding, error);
      }
    }
  };

  useEventListener(document, "keydown", handleKeydown);
};

function parseBinding(binding: string | ShortcutBinding): ShortcutBinding {
  if (typeof binding === "string")
    return {
      key: binding,
      shift: false,
      ctrl: false,
      alt: false,
      meta: false,
    };
  else {
    binding = {
      shift: false,
      ctrl: false,
      alt: false,
      meta: false,
      ...binding,
    };
  }

  if (!binding.meta) return binding;
  const { isMac } = useDevice();
  if (isMac) {
    // on Mac, treat ctrl as meta
    if (binding.ctrl) {
      binding.meta = true;
      binding.ctrl = false;
    }
  } else {
    // on non-Mac, treat meta as ctrl
    if (binding.meta) {
      binding.ctrl = true;
      binding.meta = false;
    }
  }
  return binding;
}

function registerShortcut(binding: ShortcutBinding) {
  const exists = shortcutsList.value.some((shortcut) => {
    return (
      shortcut.key === binding.key &&
      shortcut.shift === binding.shift &&
      shortcut.ctrl === binding.ctrl &&
      shortcut.alt === binding.alt &&
      shortcut.meta === binding.meta
    );
  });

  if (!exists) {
    shortcutsList.value.push(binding);
  }
}

function isEventRegistered(
  e: KeyboardEvent,
  shortcutBinding: ShortcutBinding
): boolean {
  return shortcutsList.value.some((shortcut) => {
    return (
      shortcut.key === shortcutBinding.key &&
      shortcut.shift === shortcutBinding.shift &&
      shortcut.ctrl === shortcutBinding.ctrl &&
      shortcut.alt === shortcutBinding.alt &&
      shortcut.meta === shortcutBinding.meta
    );
  });
}

function disableShortcuts(): boolean {
  const activeElement = document.activeElement;
  return (
    activeElement instanceof HTMLInputElement ||
    activeElement instanceof HTMLTextAreaElement ||
    (activeElement as any)?.contentEditable === "true" ||
    activeElement?.closest("input") ||
    activeElement?.closest("textarea") ||
    activeElement?.closest("[contenteditable]") ||
    activeElement?.closest(".dropdown-options") || // Dropdown search
    activeElement?.closest('[role="dialog"]') ||
    activeElement?.closest('[role="menu"]') ||
    activeElement?.classList.contains("form-control") // Form inputs
  );
}

function executeHandler(
  e: KeyboardEvent,
  shortcutBinding: ShortcutBinding
): boolean {
  let matches = false;

  if (
    e.key === "Shift" ||
    e.key === "Control" ||
    e.key === "Alt" ||
    e.key === "Meta"
  ) {
    return; // Ignore modifier key events
  }

  const keyMatches = e.key.toLowerCase() === shortcutBinding.key.toLowerCase();
  const shiftMatches = shortcutBinding.shift ? e.shiftKey : !e.shiftKey;
  const ctrlMatches = shortcutBinding.ctrl ? e.ctrlKey : !e.ctrlKey;
  const altMatches = shortcutBinding.alt ? e.altKey : !e.altKey;
  const metaMatches = shortcutBinding.meta ? e.metaKey : !e.metaKey;
  matches =
    keyMatches && shiftMatches && ctrlMatches && altMatches && metaMatches;

  return matches;
}
