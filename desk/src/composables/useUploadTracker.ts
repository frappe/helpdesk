import { removeAttachmentFromServer } from "@/utils";
import { computed, ref } from "vue";

interface Uploaded {
  name: string;
  url: string;
}

/**
 * Counts a composer's in-flight editor uploads so it can hold Send: a node only
 * gets its `src` when the upload resolves, so sending early stores an empty one.
 */
export function useUploadTracker() {
  const inFlight = ref(0);
  // what this editor uploaded; the paperclip's own uploads never land here
  const uploaded: Uploaded[] = [];
  // the same uploads, awaited so a drop cannot run before they register
  let landing: Promise<unknown>[] = [];

  function track<T>(upload: Promise<T>): Promise<T> {
    inFlight.value += 1;
    landing.push(
      upload
        .then((file) => {
          const { name, file_url: url } = (file ?? {}) as {
            name?: string;
            file_url?: string;
          };
          if (name && url) uploaded.push({ name, url });
        })
        .catch(() => {})
    );
    return upload.finally(() => (inFlight.value -= 1));
  }

  /**
   * Deletes what this editor uploaded and the content no longer shows; a pasted
   * image is attached the moment it lands. Call it where the content is final
   * (send, discard, unmount), not on removal, which would break undo and cut.
   * ponytail: a crash still leaks the file; needs a server-side sweep.
   */
  async function dropUnused(content: string | null) {
    // Discard is live during an upload, so wait for it to register or it leaks
    await Promise.allSettled(landing);
    landing = [];
    const keep = content ?? "";
    const stale = uploaded.filter((f) => !keep.includes(f.url));
    uploaded.length = 0;
    await Promise.allSettled(
      stale.map((f) => removeAttachmentFromServer(f.name))
    );
  }

  return {
    isUploading: computed(() => inFlight.value > 0),
    track,
    dropUnused,
  };
}
