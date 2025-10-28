import { computed } from "vue";
import { __, translationsLoaded } from "@/translation";

/**
 * Composable for reactive translations
 * Returns a computed property that re-evaluates when translations are loaded
 */
export function useTranslation(key: string) {
  return computed(() => {
    // Access translationsLoaded to create reactive dependency
    translationsLoaded.value;
    return __(key);
  });
}

/**
 * Helper for multiple translations
 */
export function useTranslations<T extends Record<string, string>>(
  keys: T
): { [K in keyof T]: ReturnType<typeof computed<string>> } {
  const result = {} as any;
  for (const [key, value] of Object.entries(keys)) {
    result[key] = computed(() => {
      translationsLoaded.value;
      return __(value);
    });
  }
  return result;
}

