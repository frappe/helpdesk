import { showCommentBox, showEmailBox } from "@/pages/ticket/modalStates";
import { computed, ref, onBeforeUnmount, getCurrentInstance } from "vue";

interface ShortcutBinding {
  key: string;
  shift?: boolean;
  ctrl?: boolean;
  alt?: boolean;
  meta?: boolean; // Cmd on Mac
}

export const shortcutsList = ref<ShortcutBinding[]>([]);
export const isShortcutsDisabled = computed(() => {
  return showEmailBox.value || showCommentBox.value;
});

export const useShortcut = (
  binding: string | ShortcutBinding,
  cb: Function
) => {
  // Normalize the binding to a consistent format
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
  } else {
    console.warn(
      `Shortcut conflict: ${shortcutBinding.key} already registered`
    );
  }

  const handleKeydown = (e: KeyboardEvent) => {
    if (isShortcutsDisabled.value) return;

    // Disable shortcuts when typing in input, textarea, or contenteditable elements
    const activeElement = document.activeElement;
    const isTypingInInput =
      activeElement instanceof HTMLInputElement ||
      activeElement instanceof HTMLTextAreaElement ||
      (activeElement as any)?.contentEditable === "true" ||
      activeElement?.closest("input") ||
      activeElement?.closest("textarea") ||
      activeElement?.closest("[contenteditable]") ||
      activeElement?.closest(".dropdown-options") || // Dropdown search
      activeElement?.classList.contains("form-control"); // Form inputs

    if (isTypingInInput) {
      return; // Don't trigger shortcuts when typing
    }

    // Create binding from the current key event
    const eventBinding: ShortcutBinding = {
      key: e.key.toLowerCase(),
      shift: e.shiftKey,
      ctrl: e.ctrlKey,
      alt: e.altKey,
      meta: e.metaKey,
    };

    // Check if this key combination is registered
    const isRegistered = shortcutsList.value.some((shortcut) => {
      return (
        shortcut.key === eventBinding.key &&
        shortcut.shift === eventBinding.shift &&
        shortcut.ctrl === eventBinding.ctrl &&
        shortcut.alt === eventBinding.alt &&
        shortcut.meta === eventBinding.meta
      );
    });

    // If not registered, don't execute further
    if (!isRegistered) {
      return;
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

  function removeShortcut() {
    shortcutsList.value = shortcutsList.value.filter((shortcut) => {
      return !(
        shortcut.key === shortcutBinding.key &&
        shortcut.shift === shortcutBinding.shift &&
        shortcut.ctrl === shortcutBinding.ctrl &&
        shortcut.alt === shortcutBinding.alt &&
        shortcut.meta === shortcutBinding.meta
      );
    });
  }

  window.addEventListener("keydown", handleKeydown);

  const instance = getCurrentInstance();
  if (instance) {
    onBeforeUnmount(() => {
      window.removeEventListener("keydown", handleKeydown);
      removeShortcut();
    });
  }
};
