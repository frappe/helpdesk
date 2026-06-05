<template>
  <span>
    <a :href="isShowable ? undefined : url" target="_blank">
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
          v-if="isText"
          class="prose prose-sm max-w-none whitespace-pre-wrap"
        >
          {{ content }}
        </div>
        <img v-if="isImage" :src="url" class="m-auto rounded border" />
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
const kind = getKind(mimeType);
const isImage = kind === "image";
const isText = kind === "text";
const isShowable = props.url && (isText || isImage);
const icon = ICONS[kind];
const content = ref("");

function toggleDialog() {
  if (!isShowable) return;
  if (isText) {
    fetch(props.url).then((res) => res.text().then((t) => (content.value = t)));
  }
  showDialog.value = !showDialog.value;
}
</script>
