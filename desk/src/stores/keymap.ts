import { ComputedRef, ref, Ref } from "vue";
import { defineStore } from "pinia";
import { useMagicKeys } from "@vueuse/core";
import { isEqual } from "lodash";
import { useDevice } from "@/composables";

type KeyCombination = Array<string>;
type Handler = () => void;
type Help = string;

const { isMac, controlKey, altKey, metaKey } = useDevice();

class Shortcut {
  constructor(
    public isActive: ComputedRef<boolean>,
    public keyCombination: KeyCombination,
    public handler: Handler,
    public help?: Help
  ) {}

  get display() {
    return this.keyCombination.map((key) => {
      switch (key) {
        case "Control":
          return controlKey;
        case "Alt":
          return altKey;
        case "Meta":
          return metaKey;
        default:
          return key;
      }
    });
  }
}

export const useKeymapStore = defineStore("keymap", () => {
  const keys = useMagicKeys({
    passive: false,
    onEventFired(e) {
      const k = items.value.find((item) => item.isActive);
      if (!k) return;

      e.preventDefault();
      k.handler();
    },
  });
  const items: Ref<Array<Shortcut>> = ref([]);
  const isOpen = ref(false);

  function add(combination: KeyCombination, handler: Handler, help?: Help) {
    const combo = Array.isArray(combination) ? combination : [combination];
    remove(combo);

    const translated = translate(combo);
    const isActive = keys[translated.join("+")];
    const s = new Shortcut(isActive, translated, handler, help);

    items.value.push(s);
  }

  function remove(combo: KeyCombination) {
    const translated = translate(combo);
    items.value = items.value.filter(
      (s) => !isEqual(s.keyCombination, translated)
    );
  }

  function toggleVisibility(open?: boolean) {
    isOpen.value = open ?? !isOpen.value;
  }

  function translate(combo: KeyCombination) {
    if (!isMac) return combo;
    return combo.map((key) => {
      if (key === "Control") return "Meta";
      else return key;
    });
  }

  return {
    add,
    isOpen,
    items,
    remove,
    toggleVisibility,
  };
});
