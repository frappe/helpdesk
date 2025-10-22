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
  binding = parseBinding(binding);
  const shortcutBinding: ShortcutBinding =
    typeof binding === "string"
      ? { key: binding, shift: false, ctrl: false, alt: false, meta: false }
      : {
          shift: false,
          ctrl: false,
          alt: false,
          meta: false,
          ...binding,
        };

  // Register shortcut immediately when useShortcut is called
  const exists = shortcutsList.value.some((shortcut) => {
    return (
      shortcut.key === shortcutBinding.key &&
      shortcut.shift === shortcutBinding.shift &&
      shortcut.ctrl === shortcutBinding.ctrl &&
      shortcut.alt === shortcutBinding.alt &&
      shortcut.meta === shortcutBinding.meta
    );
  });

  if (!exists) {
    shortcutsList.value.push(shortcutBinding);
  }

  const handleKeydown = (e: KeyboardEvent) => {
    // Disable shortcuts when typing in input, textarea, or contenteditable elements
    // if event is not registered, return
    if (!isEventRegistered(e)) {
      return;
    }
    const activeElement = document.activeElement;

    if (disableShortcuts()) {
      return; // Don't trigger shortcuts when typing, or in modals/menus
    }

    // Check if this specific handler should execute
    let matches = false;

    if (typeof binding === "string") {
      const keyMatches = e.key.toLowerCase() === binding.toLowerCase();
      const noModifiers = !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey;
      matches = keyMatches && noModifiers;
    } else {
      // Complex binding with modifiers
      if (
        e.key === "Shift" ||
        e.key === "Control" ||
        e.key === "Alt" ||
        e.key === "Meta"
      ) {
        return; // Ignore modifier key events
      }
      const keyMatches = e.key.toLowerCase() === binding.key.toLowerCase();
      const shiftMatches = binding.shift ? e.shiftKey : !e.shiftKey;
      const ctrlMatches = binding.ctrl ? e.ctrlKey : !e.ctrlKey;
      const altMatches = binding.alt ? e.altKey : !e.altKey;
      const metaMatches = binding.meta ? e.metaKey : !e.metaKey;
      matches =
        keyMatches && shiftMatches && ctrlMatches && altMatches && metaMatches;
    }

    if (matches) {
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

function isEventRegistered(e): boolean {
  const eventBinding: ShortcutBinding = {
    key: e.key.toLowerCase(),
    shift: e.shiftKey,
    ctrl: e.ctrlKey,
    alt: e.altKey,
    meta: e.metaKey,
  };

  return shortcutsList.value.some((shortcut) => {
    return (
      shortcut.key === eventBinding.key &&
      shortcut.shift === eventBinding.shift &&
      shortcut.ctrl === eventBinding.ctrl &&
      shortcut.alt === eventBinding.alt &&
      shortcut.meta === eventBinding.meta
    );
  });
}

function parseBinding(binding: string | ShortcutBinding): ShortcutBinding {
  if (typeof binding === "string") return binding;

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
