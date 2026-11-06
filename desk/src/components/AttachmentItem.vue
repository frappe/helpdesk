<template>
  <span>
    <a :href="preview ? undefined : url" target="_blank">
      <Button
        :label="label"
        theme="gray"
        variant="outline"
        @click="toggleDialog()"
      >
        <template #prefix>
          <LucidePaperclip class="h-4 w-4" />
        </template>
        <template #suffix>
          <slot name="suffix" />
        </template>
      </Button>
    </a>
    <Dialog v-model:open="showDialog" :title="label" size="4xl">
      <template #default>
        <div
          v-if="preview === 'text'"
          class="prose prose-sm max-w-none whitespace-pre-wrap"
        >
          {{ content }}
        </div>
        <img
          v-if="preview === 'image'"
          :src="url"
          class="m-auto rounded-4 border"
        />
        <video
          v-if="preview === 'video'"
          :src="url"
          controls
          class="m-auto max-h-[70vh] rounded-4 border"
        />
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { Button, Dialog } from "frappe-ui";
import { getType as getMime } from "mime";
import { ref } from "vue";
import LucidePaperclip from "~icons/lucide/paperclip";

interface P {
  label: string;
  url?: string | null;
}

const props = withDefaults(defineProps<P>(), {
  url: null,
});

// browsers render only some image/video mimes (.dwg is image/vnd.dwg, .avi is
// video/x-msvideo) — anything absent here becomes a download link like pdf
type Preview = "image" | "video" | "text";

const PREVIEWS: Record<string, Preview> = {
  "image/png": "image",
  "image/jpeg": "image",
  "image/gif": "image",
  "image/webp": "image",
  "image/svg+xml": "image",
  "image/avif": "image",
  "image/bmp": "image",
  "image/apng": "image",
  "image/vnd.microsoft.icon": "image",
  "video/mp4": "video",
  "video/webm": "video",
  "video/ogg": "video",
  "video/x-m4v": "video",
  "text/plain": "text",
};

const showDialog = ref(false);
const mimeType = getMime(props.label) || "";
const preview = props.url ? PREVIEWS[mimeType] : undefined;
const content = ref("");

function toggleDialog() {
  if (!preview) return;
  if (preview === "text") {
    fetch(props.url).then((res) => res.text().then((t) => (content.value = t)));
  }
  showDialog.value = !showDialog.value;
}
</script>
