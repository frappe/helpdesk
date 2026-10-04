<template>
  <div class="flex flex-row flex-wrap gap-2 pt-4">
    <Button
      v-for="(attachment, index) in attachments"
      :key="attachment.file_url"
      variant="outline"
      class="max-w-full"
      :label="attachment.file_name"
      :icon-left="iconOf(attachment)"
      @click="openAttachment(index)"
    />

    <Dialog v-model:open="showDialog" size="4xl">
      <template #title>
        <div class="flex min-w-0 items-center justify-between gap-3">
          <div
            class="flex min-w-0 items-baseline gap-2 truncate font-medium text-ink-gray-9"
          >
            {{ current?.file_name }}
            <span
              v-if="viewable.length > 1"
              class="shrink-0 text-p-xs font-normal text-ink-gray-5"
            >
              {{ __("{0} of {1}", [position + 1, viewable.length]) }}
            </span>
          </div>
          <div class="flex shrink-0 items-center gap-1">
            <Button
              v-if="viewable.length > 1"
              variant="ghost"
              icon="lucide-chevron-left"
              :disabled="position === 0"
              :aria-label="__('Previous attachment')"
              @click="showAdjacent(-1)"
            />
            <Button
              v-if="viewable.length > 1"
              variant="ghost"
              icon="lucide-chevron-right"
              :disabled="position === viewable.length - 1"
              :aria-label="__('Next attachment')"
              @click="showAdjacent(1)"
            />
            <Button
              variant="ghost"
              icon="lucide-external-link"
              :aria-label="__('Open in a new tab')"
              @click="openInTab(current)"
            />
          </div>
        </div>
      </template>

      <div class="flex justify-center">
        <img
          v-if="kindOf(current) === 'image'"
          :src="current?.file_url"
          :alt="current?.file_name"
          class="m-auto max-h-[70vh] max-w-full rounded-5 border border-outline-gray-2"
        />
        <video
          v-else-if="kindOf(current) === 'video'"
          :src="current?.file_url"
          controls
          class="m-auto max-h-[70vh] max-w-full rounded-5 border border-outline-gray-2"
        />
        <div
          v-else
          class="prose prose-sm max-h-[70vh] w-full max-w-none overflow-auto whitespace-pre-wrap font-mono text-p-sm text-ink-gray-8"
        >
          {{ text }}
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, Dialog } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";

interface Attachment {
  file_url: string;
  file_name: string;
}

type Kind = "image" | "video" | "text" | "pdf" | "spreadsheet" | "file";

// By extension: the payload carries a name and a URL, not a mime type.
const KINDS: Record<string, Kind> = {
  png: "image",
  jpg: "image",
  jpeg: "image",
  gif: "image",
  webp: "image",
  svg: "image",
  bmp: "image",
  avif: "image",
  heic: "image",
  mp4: "video",
  mov: "video",
  webm: "video",
  m4v: "video",
  ogv: "video",
  txt: "text",
  log: "text",
  md: "text",
  csv: "text",
  json: "text",
  pdf: "pdf",
  xls: "spreadsheet",
  xlsx: "spreadsheet",
  ods: "spreadsheet",
};

const ICONS: Record<Kind, string> = {
  image: "lucide-file-image",
  video: "lucide-file-video",
  text: "lucide-file-type",
  pdf: "lucide-file-text",
  spreadsheet: "lucide-file-spreadsheet",
  file: "lucide-file",
};

const VIEWABLE: Kind[] = ["image", "video", "text"];

const props = withDefaults(defineProps<{ attachments?: Attachment[] }>(), {
  attachments: () => [],
});

const showDialog = ref(false);
const position = ref(0);
const text = ref("");

const viewable = computed(() => props.attachments.filter(isViewable));
const current = computed(() => viewable.value[position.value] || null);

function kindOf(attachment?: Attachment | null): Kind {
  const extension =
    (attachment?.file_name || "").split(".").pop()?.toLowerCase() || "";
  return KINDS[extension] || "file";
}

function iconOf(attachment: Attachment) {
  return ICONS[kindOf(attachment)];
}

function isViewable(attachment: Attachment) {
  return VIEWABLE.includes(kindOf(attachment));
}

function openAttachment(index: number) {
  const attachment = props.attachments[index];
  if (!isViewable(attachment)) return openInTab(attachment);
  position.value = viewable.value.indexOf(attachment);
  showDialog.value = true;
}

function showAdjacent(by: number) {
  const next = position.value + by;
  if (next < 0 || next >= viewable.value.length) return;
  position.value = next;
}

function openInTab(attachment?: Attachment | null) {
  if (attachment) window.open(attachment.file_url, "_blank");
}

watch([current, showDialog], () => {
  text.value = "";
  if (!showDialog.value || !current.value || kindOf(current.value) !== "text")
    return;
  const url = current.value.file_url;
  fetch(url)
    .then((response) => response.text())
    .then((body) => {
      // The reader may have stepped on while this was in flight.
      if (current.value?.file_url === url) text.value = body;
    })
    .catch(() => (text.value = __("This file could not be read.")));
});
</script>
