import { reactive } from "vue";
import { Action, Key } from "./types";

export const selection = reactive({
  storage: new Set<Key>(),
  actions: new Set<Action>(),
  toggle: (key: Key) => {
    if (!selection.storage.delete(key)) {
      selection.storage.add(key);
    }
  },
  reset: () => {
    selection.storage.clear();
    selection.actions.clear();
  },
});
