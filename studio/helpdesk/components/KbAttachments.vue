<template>
  <div class="kb-attachments">
    <Button
      v-for="(attachment, index) in attachments"
      :key="attachment.file_url"
      variant="outline"
      :label="attachment.file_name"
      :icon-left="iconOf(attachment)"
      @click="open(index)"
    />

    <Dialog v-model="showDialog" size="4xl">
      <template #title>
        <div class="kb-attachments__head">
          <div class="kb-attachments__title">
            {{ current?.file_name }}
            <!-- Which of how many, the way any gallery says it. Only worth saying when
                 there is more than one to step through. -->
            <span v-if="viewable.length > 1" class="kb-attachments__count">
              {{ position + 1 }} of {{ viewable.length }}
            </span>
          </div>
          <div class="kb-attachments__controls">
            <Button
              v-if="viewable.length > 1"
              variant="ghost"
              icon="lucide-chevron-left"
              :disabled="position === 0"
              aria-label="Previous attachment"
              @click="step(-1)"
            />
            <Button
              v-if="viewable.length > 1"
              variant="ghost"
              icon="lucide-chevron-right"
              :disabled="position === viewable.length - 1"
              aria-label="Next attachment"
              @click="step(1)"
            />
            <Button
              variant="ghost"
              icon="lucide-external-link"
              aria-label="Open in a new tab"
              @click="openInTab(current)"
            />
          </div>
        </div>
      </template>

      <template #body-content>
        <div class="kb-attachments__body">
          <img
            v-if="kindOf(current) === 'image'"
            :src="current?.file_url"
            :alt="current?.file_name"
            class="kb-attachments__media"
          />
          <video
            v-else-if="kindOf(current) === 'video'"
            :src="current?.file_url"
            controls
            class="kb-attachments__media"
          />
          <div v-else class="kb-attachments__text prose prose-sm">
            {{ text }}
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
// A message's attachments, and the viewer behind them — the agent portal's
// `desk/src/components/AttachmentItem.vue`: the same file-kind icon on the chip, the same
// 4xl dialog, images and video centred, plain text read out as text. Anything the browser
// cannot show inline (a PDF, a spreadsheet) opens in a tab, as it does there.
//
// The one addition: a message often carries several files, so the dialog steps between
// them instead of making the reader close it and pick the next chip.
import { computed, ref, watch } from "vue";
import { Button, Dialog } from "frappe-ui";

interface Attachment {
  file_url: string;
  file_name: string;
}

const props = withDefaults(defineProps<{ attachments?: Attachment[] }>(), {
  attachments: () => [],
});

type Kind = "image" | "video" | "text" | "pdf" | "spreadsheet" | "file";

// By extension: the payload carries a name and a URL, not a mime type, and the desk's
// `mime` lookup keys off the name in the end too.
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

/** What the dialog can show; the rest belong in a tab. */
const VIEWABLE: Kind[] = ["image", "video", "text"];

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

function open(index: number) {
  const attachment = props.attachments[index];
  if (!isViewable(attachment)) return openInTab(attachment);
  position.value = viewable.value.indexOf(attachment);
  showDialog.value = true;
}

function step(by: number) {
  const next = position.value + by;
  if (next < 0 || next >= viewable.value.length) return;
  position.value = next;
}

function openInTab(attachment?: Attachment | null) {
  if (attachment) window.open(attachment.file_url, "_blank");
}

// A text file has to be fetched before it can be read; images and video are fetched by
// the elements themselves.
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
    .catch(() => (text.value = "This file could not be read."));
});
</script>

<style scoped>
.kb-attachments {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 16px;
}

.kb-attachments__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.kb-attachments__title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
  color: var(--ink-gray-9);
}

.kb-attachments__count {
  flex-shrink: 0;
  font-weight: 400;
  font-size: 12px;
  color: var(--ink-gray-5);
}

.kb-attachments__controls {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.kb-attachments__body {
  display: flex;
  justify-content: center;
}

.kb-attachments__media {
  max-height: 70vh;
  max-width: 100%;
  margin: auto;
  border: 1px solid var(--outline-gray-2);
  border-radius: 6px;
}

.kb-attachments__text {
  max-height: 70vh;
  width: 100%;
  overflow: auto;
  white-space: pre-wrap;
  max-width: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px;
  color: var(--ink-gray-8);
}
</style>
