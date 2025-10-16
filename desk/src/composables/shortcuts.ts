import { showCommentBox, showEmailBox } from "@/pages/ticket/modalStates";
import { computed, onBeforeUnmount, ref } from "vue";

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
    let matches = false;

    // means if binding is a string, e.g., "s"
    if (typeof binding === "string") {
      // Simple string binding (case-insensitive)
      matches = e.key.toLowerCase() === binding.toLowerCase();
    }
    // means it is a combination of keys like Shift+S or Ctrl+S ({ key: "s", shift: true })
    else {
      // Complex binding with modifiers
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
      shortcutsList.value.push(binding as ShortcutBinding);
    }

    if (matches) {
      e.preventDefault();
      cb();
    }
  };

  window.addEventListener("keydown", handleKeydown);

  onBeforeUnmount(() => {
    window.removeEventListener("keydown", handleKeydown);
  });
};
