<template>
  <div class="flex flex-col gap-1.5">
    <span class="text-p-sm text-ink-gray-5">{{ __('Attachments') }}</span>

    <div
      class="flex flex-col rounded-6 border transition-colors"
      :class="[
        uploader.items.length ? 'divide-y divide-outline-gray-1' : 'border-dashed',
        dragging ? 'border-outline-gray-4 bg-surface-gray-1' : 'border-outline-gray-2',
      ]"
      @dragenter.prevent="dragging = true"
      @dragover.prevent="dragging = true"
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
    >
      <div
        v-for="item in uploader.items"
        :key="item.id"
        class="flex items-center gap-3 px-3 py-2"
      >
        <span
          class="grid size-9 shrink-0 place-items-center overflow-hidden rounded-4 border border-outline-gray-1 bg-surface-gray-1"
        >
          <Spinner v-if="isBusy(item)" size="md" class="text-ink-gray-5" />
          <LucideCircleAlert v-else-if="item.status === 'error'" class="size-4 text-ink-red-4" />
          <img
            v-else-if="isImage(item.name)"
            :src="item.fileUrl"
            :alt="item.name"
            class="size-full object-cover"
          />
          <LucideFile v-else class="size-4 text-ink-gray-5" />
        </span>
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <a
            v-if="item.status === 'done'"
            :href="item.fileUrl"
            target="_blank"
            rel="noopener"
            class="truncate text-p-sm text-ink-gray-8 hover:underline"
          >
            {{ item.name }}
          </a>
          <span v-else class="truncate text-p-sm text-ink-gray-8">{{ item.name }}</span>
          <span
            class="text-p-xs"
            :class="item.status === 'error' ? 'text-ink-red-4' : 'text-ink-gray-5'"
          >
            {{ meta(item) }}
          </span>
        </div>
        <button
          type="button"
          :aria-label="isBusy(item) ? __('Cancel upload') : __('Remove')"
          class="grid size-7 shrink-0 place-items-center rounded-4 text-ink-gray-5 hover:bg-surface-gray-3 hover:text-ink-gray-8"
          @click="remove(item.id)"
        >
          <LucideX class="size-4" />
        </button>
      </div>

      <button
        v-if="uploader.items.length"
        type="button"
        class="group flex items-center gap-3 rounded-b-6 px-3 py-2 text-left hover:bg-surface-gray-1 focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        @click="picker?.click()"
      >
        <span
          class="grid size-9 shrink-0 place-items-center rounded-4 border border-dashed border-outline-gray-3 text-ink-gray-5 group-hover:text-ink-gray-8"
        >
          <LucidePlus class="size-4" />
        </span>
        <span class="flex-1 text-p-sm text-ink-gray-6 group-hover:text-ink-gray-8">{{ __('Add more') }}</span>
        <span class="hidden items-center gap-1.5 text-p-xs text-ink-gray-5 sm:flex">
          {{ __('drop, browse or') }}
          <KeyboardShortcut bg combo="Mod+V" />
        </span>
      </button>
      <button
        v-else
        type="button"
        class="flex items-center justify-center gap-3 rounded-6 px-4 py-6 text-p-sm text-ink-gray-5 hover:bg-surface-gray-1 focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        @click="picker?.click()"
      >
        <LucidePaperclip class="size-4" />
        <span>
          <span class="font-medium text-ink-gray-8">{{ __('Add a file') }}</span>
          {{ __('or drop files here') }}
        </span>
      </button>
    </div>

    <input ref="picker" type="file" multiple class="sr-only" :accept="accept" @change="onPick" />

    <p v-for="error in uploader.errors.value" :key="error" class="text-p-xs text-ink-red-4">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { KeyboardShortcut, Spinner } from "frappe-ui";
import { useUploader } from "@framework/ui/FileUpload";
import type { Restrictions, UploadItem, UploadResult, UploadTransport } from "@framework/ui/FileUpload";
import { __ } from "@helpdesk/shared/translation";
import LucideCircleAlert from "~icons/lucide/circle-alert";
import LucideFile from "~icons/lucide/file";
import LucidePaperclip from "~icons/lucide/paperclip";
import LucidePlus from "~icons/lucide/plus";
import LucideX from "~icons/lucide/x";

const props = defineProps<{
  modelValue: UploadResult[];
  restrictions?: Restrictions;
  transport?: UploadTransport;
}>();

const emit = defineEmits<{ "update:modelValue": [UploadResult[]] }>();

const uploader = useUploader({
  transport: props.transport,
  // useUploader keeps the object it is given; read through so later config applies
  restrictions: new Proxy({}, { get: (_, key) => props.restrictions?.[key] }),
  multiple: true,
});

const accept = computed(() => props.restrictions?.allowed_file_types?.join(","));
const dragging = ref(false);
const picker = ref<HTMLInputElement>();
let running = false;

function onPick(event: Event) {
  const input = event.target as HTMLInputElement;
  add(input.files);
  input.value = "";
}

function onDrop(event: DragEvent) {
  dragging.value = false;
  add(event.dataTransfer?.files);
}

// the description editor and inputs handle their own paste
function onPaste(event: ClipboardEvent) {
  const target = event.target as HTMLElement;
  if (target.closest("input, textarea, [contenteditable='true']")) return;
  if (!event.clipboardData?.files.length) return;
  event.preventDefault();
  add(event.clipboardData.files);
}

onMounted(() => document.addEventListener("paste", onPaste));
onBeforeUnmount(() => document.removeEventListener("paste", onPaste));

function onDragLeave(event: DragEvent) {
  const box = event.currentTarget as HTMLElement;
  if (!box.contains(event.relatedTarget as Node)) dragging.value = false;
}

function add(files?: FileList | null) {
  if (!files?.length) return;
  uploader.add(files);
  upload();
}

// commit() skips items added while a pass runs, so keep going until none are left
async function upload() {
  if (running) return;
  running = true;
  while (uploader.items.some((item) => item.status === "idle")) {
    await uploader.commit();
    emitDone();
  }
  running = false;
}

function remove(id: string) {
  uploader.remove(id);
  emitDone();
}

function emitDone() {
  emit(
    "update:modelValue",
    uploader.items
      .filter((item) => item.status === "done")
      .map((item) => ({ file_url: item.fileUrl!, file_name: item.name, is_private: item.isPrivate }))
  );
}

function isBusy(item: UploadItem) {
  return item.status === "idle" || item.status === "uploading";
}

function meta(item: UploadItem) {
  if (item.status === "error") return item.error;
  if (isBusy(item)) return __("Uploading… {0}%", [Math.round(item.progress * 100)]);
  return formatSize(item.size ?? 0);
}

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function isImage(name: string) {
  return /\.(png|jpe?g|gif|webp|svg|bmp|avif)$/i.test(name);
}
</script>
