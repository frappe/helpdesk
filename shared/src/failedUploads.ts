import { computed, ref, shallowRef } from "vue";

/**
 * Keeps the files whose upload failed, so a composer can offer Retry. A retry
 * re-uploads the same File; `clear()` drops them, and the result of a retry
 * still in flight, when the composer is sent or discarded.
 */
export function useFailedUploads<T>(
  upload: (file: File) => Promise<T>,
  onUploaded: (result: T) => void
) {
  // shallow: a deep ref would proxy the files and break `!==` in remove()
  const files = shallowRef<File[]>([]);
  const retrying = ref(0);
  let epoch = 0;

  function add(file: File) {
    files.value = [...files.value, file];
  }

  function remove(file: File) {
    files.value = files.value.filter((f) => f !== file);
  }

  async function retry(file: File) {
    const started = epoch;
    remove(file);
    retrying.value += 1;
    try {
      const result = await upload(file);
      if (started === epoch) onUploaded(result);
    } catch {
      if (started === epoch) add(file);
    } finally {
      retrying.value -= 1;
    }
  }

  function clear() {
    epoch += 1;
    files.value = [];
  }

  return {
    files,
    isRetrying: computed(() => retrying.value > 0),
    add,
    remove,
    retry,
    clear,
  };
}
