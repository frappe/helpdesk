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
          <component :is="icon" class="h-4 w-4" />
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
          class="m-auto rounded border"
        />
        <video
          v-if="preview === 'video'"
          :src="url"
          controls
          class="m-auto max-h-[70vh] rounded border"
        />
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { Button, Dialog } from "frappe-ui";
import { getType as getMime } from "mime";
import { markRaw, ref, type Component } from "vue";
import LucideFile from "~icons/lucide/file";
import LucideFileImage from "~icons/lucide/file-image";
import LucideFileSpreadsheet from "~icons/lucide/file-spreadsheet";
import LucideFileText from "~icons/lucide/file-text";
import LucideFileType from "~icons/lucide/file-type";
import LucideFileVideo from "~icons/lucide/file-video";

interface P {
  label: string;
  url?: string | null;
}

const props = withDefaults(defineProps<P>(), {
  url: null,
});

type AttachmentKind =
  | "image"
  | "video"
  | "pdf"
  | "spreadsheet"
  | "text"
  | "file";

const ICONS: Record<AttachmentKind, Component> = {
  image: markRaw(LucideFileImage),
  video: markRaw(LucideFileVideo),
  pdf: markRaw(LucideFileText),
  spreadsheet: markRaw(LucideFileSpreadsheet),
  text: markRaw(LucideFileType),
  file: markRaw(LucideFile),
};

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
  "video/mp4": "video",
  "video/webm": "video",
  "video/ogg": "video",
  "text/plain": "text",
};

function getKind(mime: string): AttachmentKind {
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("video/")) return "video";
  if (mime === "application/pdf") return "pdf";
  if (mime.includes("spreadsheet")) return "spreadsheet";
  if (mime === "text/plain") return "text";
  return "file";
}

const showDialog = ref(false);
const mimeType = getMime(props.label) || "";
const icon = ICONS[getKind(mimeType)];
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
