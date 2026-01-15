import { useDevice } from "@/composables";
import { useEventListener } from "@vueuse/core";
import { ref } from "vue";

interface ShortcutBinding {
  key: string;
  shift?: boolean;
  ctrl?: boolean;
  alt?: boolean;
  meta?: boolean; // Cmd on Mac
}

export const shortcutsList = ref<ShortcutBinding[]>([]);

// Registers a keyboard shortcut and its callback
// binding: can take either a string (key) or a ShortcutBinding object, e.g., 'k' or { key: 'k', cmnd: true }
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

    if (validateKeyCombination(e, shortcutBinding)) {
      try {
        // Don't prevent default for page navigation keys
        const navigationKeys = ['PageUp', 'PageDown', 'Home', 'End'];
        if (!navigationKeys.includes(e.key)) {
          e.preventDefault();
        }
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
  return Boolean(
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

function validateKeyCombination(
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

  const shiftMatches = shortcutBinding.shift ? e.shiftKey : !e.shiftKey;
  const ctrlMatches = shortcutBinding.ctrl ? e.ctrlKey : !e.ctrlKey;
  const altMatches = shortcutBinding.alt ? e.altKey : !e.altKey;
  const metaMatches = shortcutBinding.meta ? e.metaKey : !e.metaKey;

  const normalizedEventKey = normalizeKey(e.key.toLowerCase());
  const normalizedBindingKey = shortcutBinding.key.toLowerCase();
  const keyMatches =
    normalizedEventKey === normalizedBindingKey ||
    e.key.toLowerCase() === normalizedBindingKey;

  matches =
    keyMatches && shiftMatches && ctrlMatches && altMatches && metaMatches;

  return matches;
}

// Normalize keys that have different values with Shift modifier
// e.g., "." becomes ">" on Windows/Linux when Shift is pressed, but remains "." on Mac
function normalizeKey(key: string): string {
  const shiftKeyMap: Record<string, string> = {
    ">": ".",
    "<": ",",
    "?": "/",
    ":": ";",
    '"': "'",
    "{": "[",
    "}": "]",
    "|": "\\",
    "+": "=",
    _: "-",
    "!": "1",
    "@": "2",
    "#": "3",
    $: "4",
    "%": "5",
    "^": "6",
    "&": "7",
    "*": "8",
    "(": "9",
    ")": "0",
  };
  return shiftKeyMap[key] || key;
}
