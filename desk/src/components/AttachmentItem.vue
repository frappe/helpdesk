<template>
  <span>
    <span @click.prevent="handleEntryClick" class="cursor-pointer">
      <Button :label="label" theme="gray" variant="outline">
        <template #prefix>
          <component :is="icon" class="h-4 w-4" />
        </template>
        <template #suffix>
          <slot name="suffix" />
        </template>
      </Button>
    </span>
    <Dialog v-model:open="showDialog" :title="activeTitle" size="4xl">
      <template #default>
        <div class="flex items-center justify-between w-full">
          <button
            v-if="attachments && attachments.length > 1"
            @click="previousImage()"
            class="p-2 rounded hover:bg-surface-gray-3 text-ink-gray-5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 flex-shrink-0"
            aria-label="Previous Attachment"
          >
            <LucideChevronLeft class="w-6 h-6" />
          </button>

          <div
            class="flex-1 flex items-center justify-center px-4 h-[60vh] overflow-hidden"
          >
            <div
              v-if="isText"
              class="w-full h-full flex flex-col bg-surface-gray-7 rounded border border-outline-gray-3 overflow-hidden relative"
            >
              <div class="absolute top-4 right-4 z-10">
                <a
                  :href="activeUrl"
                  target="_blank"
                  class="px-3 py-1.5 bg-surface-gray-2 hover:bg-surface-gray-3 text-ink-gray-9 text-xs rounded transition-colors border border-outline-gray-3 font-medium shadow-sm"
                >
                  Open Raw
                </a>
              </div>
              <div class="flex-1 overflow-auto p-4">
                <pre
                  class="text-xs font-mono text-ink-gray-3 whitespace-pre-wrap break-all"
                  >{{ content || "Loading text..." }}</pre
                >
              </div>
            </div>

            <div
              v-else-if="isImage"
              class="relative w-full h-full flex items-center justify-center"
            >
              <div
                v-show="!isImageLoaded"
                class="absolute inset-0 flex items-center justify-center"
              >
                <div
                  class="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-gray-5"
                ></div>
              </div>
              <img
                :src="activeUrl"
                @load="isImageLoaded = true"
                :class="{
                  'opacity-0': !isImageLoaded,
                  'opacity-100': isImageLoaded,
                }"
                class="max-w-full max-h-full object-contain rounded shadow-sm bg-white transition-opacity duration-200"
              />
            </div>

            <div
              v-else
              class="flex flex-col items-center justify-center space-y-4"
            >
              <component
                :is="ICONS[activeKind]"
                class="w-24 h-24 text-ink-gray-4"
              />
              <p
                class="text-ink-gray-7 text-lg font-medium text-center truncate max-w-md"
              >
                {{ activeAttachment.file_name }}
              </p>
              <a
                :href="activeUrl"
                target="_blank"
                class="px-5 py-2 bg-surface-gray-2 hover:bg-surface-gray-3 text-ink-gray-9 rounded-md transition-colors border border-outline-gray-3 font-medium shadow-sm"
              >
                Open File
              </a>
            </div>
          </div>

          <button
            v-if="attachments && attachments.length > 1"
            @click="nextImage()"
            class="p-2 rounded hover:bg-surface-gray-3 text-ink-gray-5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 flex-shrink-0"
            aria-label="Next Attachment"
          >
            <LucideChevronRight class="w-6 h-6" />
          </button>
        </div>
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { Button, Dialog } from "frappe-ui";
import { getType as getMime } from "mime";
import {
  markRaw,
  ref,
  computed,
  watch,
  onBeforeUnmount,
  type Component,
} from "vue";
import LucideFile from "~icons/lucide/file";
import LucideFileImage from "~icons/lucide/file-image";
import LucideFileSpreadsheet from "~icons/lucide/file-spreadsheet";
import LucideFileText from "~icons/lucide/file-text";
import LucideFileType from "~icons/lucide/file-type";
import LucideFileVideo from "~icons/lucide/file-video";
import LucideChevronLeft from "~icons/lucide/chevron-left";
import LucideChevronRight from "~icons/lucide/chevron-right";

interface Attachment {
  file_url: string;
  file_name?: string;
  [key: string]: any;
}

interface P {
  label: string;
  url?: string | null;
  attachments?: Attachment[];
}

type AttachmentKind =
  | "image"
  | "video"
  | "pdf"
  | "spreadsheet"
  | "text"
  | "file";

const props = withDefaults(defineProps<P>(), {
  url: null,
});

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
const content = ref("");
const currentIndex = ref(0);
const isImageLoaded = ref(false);

const buttonKind = getKind(getMime(props.label) || "");
const icon = ICONS[buttonKind];

const isShowable = computed(() => {
  if (props.attachments && props.attachments.length > 0) return true;
  return !!props.url && (buttonKind === "text" || buttonKind === "image");
});

const activeAttachment = computed(() =>
  props.attachments && props.attachments.length > 0
    ? props.attachments[currentIndex.value]
    : { file_url: props.url, file_name: props.label }
);

const activeUrl = computed(() => activeAttachment.value.file_url);

const activeTitle = computed(() => {
  const name = activeAttachment.value.file_name || "";
  if (name.length <= 60) return name;

  const lastDotIndex = name.lastIndexOf(".");
  if (lastDotIndex === -1 || lastDotIndex === 0) {
    return name.substring(0, 57) + "...";
  }

  const ext = name.substring(lastDotIndex);
  const baseName = name.substring(0, lastDotIndex);
  const keepLength = 60 - ext.length - 3;
  return baseName.substring(0, keepLength) + "..." + ext;
});

const activeKind = computed(() =>
  getKind(getMime(activeAttachment.value.file_name || "") || "")
);
const isImage = computed(() => activeKind.value === "image");
const isText = computed(() => activeKind.value === "text");

function nextImage() {
  if (!props.attachments) return;
  currentIndex.value =
    currentIndex.value < props.attachments.length - 1
      ? currentIndex.value + 1
      : 0;
}

function previousImage() {
  if (!props.attachments) return;
  currentIndex.value =
    currentIndex.value > 0
      ? currentIndex.value - 1
      : props.attachments.length - 1;
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "ArrowRight") nextImage();
  if (e.key === "ArrowLeft") previousImage();
}

let abortController: AbortController | null = null;

watch(
  [activeUrl, showDialog],
  async ([newUrl, isOpen]) => {
    isImageLoaded.value = false;

    // Sync keyboard listener with dialog open state
    if (isOpen) {
      window.addEventListener("keydown", handleKeydown);
    } else {
      window.removeEventListener("keydown", handleKeydown);
    }

    // Kill any in-flight fetch
    if (abortController) {
      abortController.abort();
      abortController = null;
    }

    if (isOpen && isText.value && newUrl) {
      abortController = new AbortController();
      content.value = "Loading text...";
      try {
        const res = await fetch(newUrl as string, {
          signal: abortController.signal,
        });
        content.value = await res.text();
      } catch (e: any) {
        if (e.name !== "AbortError") {
          content.value = "Error loading file content.";
        }
      } finally {
        abortController = null;
      }
    } else if (!isOpen) {
      content.value = "";
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeydown);
  if (abortController) abortController.abort();
});

function toggleDialog() {
  if (!isShowable.value) return;

  // If a specific url is passed alongside a carousel, jump to that attachment
  if (props.attachments && props.url) {
    const foundIndex = props.attachments.findIndex(
      (a) => a.file_url === props.url
    );
    if (foundIndex !== -1) currentIndex.value = foundIndex;
  }

  showDialog.value = !showDialog.value;
}

function handleEntryClick() {
  if (isShowable.value) {
    toggleDialog();
  } else if (props.url) {
    window.open(props.url, "_blank");
  } else {
    console.warn("AttachmentItem: No valid URL or attachments provided.");
  }
}
</script>
