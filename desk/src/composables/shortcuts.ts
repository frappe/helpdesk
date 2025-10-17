import { showCommentBox, showEmailBox } from "@/pages/ticket/modalStates";
import { computed, ref } from "vue";

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

    let matches = false;

    // means if binding is a string, e.g., "s"
    if (typeof binding === "string") {
      const keyMatches = e.key.toLowerCase() === binding.toLowerCase();
      const noModifiers = !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey;

      matches = keyMatches && noModifiers; // This prevents the overlap
    }
    // means it is a combination of keys like Shift+S or Ctrl+S ({ key: "s", shift: true })
    else {
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
    // validate if the shortcut already exists in the list
    const exists = shortcutsList.value.some((shortcut) => {
      return (
        shortcut.key ===
          (typeof binding === "string" ? binding : binding.key) &&
        shortcut.shift ===
          (typeof binding === "string" ? false : binding.shift) &&
        shortcut.ctrl ===
          (typeof binding === "string" ? false : binding.ctrl) &&
        shortcut.alt === (typeof binding === "string" ? false : binding.alt) &&
        shortcut.meta === (typeof binding === "string" ? false : binding.meta)
      );
    });

    if (!exists) {
      // FIXED: Properly convert string to ShortcutBinding
      const shortcutBinding: ShortcutBinding =
        typeof binding === "string"
          ? { key: binding, shift: false, ctrl: false, alt: false, meta: false }
          : binding;

      shortcutsList.value.push(shortcutBinding);
    }

    if (matches) {
      e.preventDefault();
      cb();
    }
  };

  window.addEventListener("keydown", handleKeydown);

  return () => {
    window.removeEventListener("keydown", handleKeydown);
  };
};
