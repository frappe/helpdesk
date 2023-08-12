import { useStorage } from "@vueuse/core";

export function useColumns(key: string) {
  const prefix = "hide_columns_";
  const storageKey = prefix + key;
  const storage = useStorage(storageKey, new Set());

  function toggle(key: string): void {
    if (!storage.value.delete(key)) {
      storage.value.add(key);
    }
  }

  return {
    storage,
    toggle,
  };
}
