import { useRoute } from "vue-router";
import { useStorage } from "@vueuse/core";

/**
 * @param doctype - The DocType to use
 */
export function useColumns(doctype: string) {
  const route = useRoute();
  const prefix = "hide_columns";
  const storageKey = [prefix, route.path, doctype].join("_");
  const storage = useStorage(storageKey, new Set());

  /**
   * @param key - The column key to toggle
   * @returns void
   * @description Toggles the column visibility
   */
  function toggle(key: string) {
    if (!storage.value.delete(key)) {
      storage.value.add(key);
    }
  }

  return {
    storage,
    toggle,
  };
}
