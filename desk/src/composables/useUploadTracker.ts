import { computed, ref } from "vue";

/**
 * Counts the editor uploads a composer has in flight, so it can hold Send until
 * they land. A media node only gets its `src` when its upload resolves, and the
 * in-flight attributes are never serialised, so sending early stores a node
 * with nothing behind it and no way to recover the file.
 */
export function useUploadTracker() {
  const inFlight = ref(0);

  /** Wrap an upload promise; pass it straight through to the editor. */
  function track<T>(upload: Promise<T>): Promise<T> {
    inFlight.value += 1;
    return upload.finally(() => (inFlight.value -= 1));
  }

  return { isUploading: computed(() => inFlight.value > 0), track };
}
