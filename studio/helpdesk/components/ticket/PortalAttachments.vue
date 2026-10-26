<template>
  <!-- `relative` keeps the sr-only picker inside the page's scroller; anchored to
       <body> it overflows it, and the whole page scrolls past its bottom. -->
  <div class="relative flex flex-col gap-1.5">
    <span class="text-p-sm text-ink-gray-5">{{ __("Attachments") }}</span>

    <div
      class="flex flex-col rounded-6 border transition-colors"
      :class="[
        uploader.items.length
          ? 'divide-y divide-outline-gray-1'
          : 'border-dashed',
        dragging
          ? 'border-outline-gray-4 bg-surface-gray-1'
          : 'border-outline-gray-2',
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
          <LucideCircleAlert
            v-else-if="item.status === 'error'"
            class="size-4 text-ink-red-6"
          />
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
          <span v-else class="truncate text-p-sm text-ink-gray-8">{{
            item.name
          }}</span>
          <span
            class="text-p-xs [overflow-wrap:anywhere]"
            :class="
              item.status === 'error' ? 'text-ink-red-6' : 'text-ink-gray-5'
            "
          >
            {{ meta(item) }}
          </span>
        </div>
        <button
          v-if="item.status === 'error'"
          type="button"
          :aria-label="__('Retry uploading {0}', [item.name])"
          :title="__('Retry upload')"
          class="grid size-7 shrink-0 place-items-center rounded-4 text-ink-gray-5 hover:bg-surface-gray-3 hover:text-ink-gray-8"
          @click="retry(item.id)"
        >
          <LucideRotateCw class="size-4" />
        </button>
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
        <span
          class="flex-1 text-p-sm text-ink-gray-6 group-hover:text-ink-gray-8"
          >{{ __("Add more") }}</span
        >
        <span
          class="hidden items-center gap-1.5 text-p-xs text-ink-gray-5 sm:flex [@media(pointer:coarse)]:hidden"
        >
          {{ __("drop, browse or") }}
          <ShortcutKey :keys="`${metaIcon} V`" />
        </span>
      </button>
      <button
        v-else
        type="button"
        class="flex items-center justify-center gap-3 rounded-6 px-4 py-6 text-p-sm text-ink-gray-5 hover:bg-surface-gray-1 focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        @click="picker?.click()"
      >
        <LucidePaperclip class="size-4" />
        <span>{{ __("Drag or paste files here, or click to browse") }}</span>
      </button>
    </div>

    <input
      ref="picker"
      type="file"
      multiple
      class="sr-only"
      :accept="accept"
      @change="onPick"
    />

    <p
      v-for="error in uploader.errors.value"
      :key="error"
      class="text-p-xs text-ink-red-6"
    >
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { Spinner, call } from "frappe-ui";
import { useUploader } from "@framework/ui/FileUpload";
import type {
  Restrictions,
  UploadItem,
  UploadResult,
  UploadTransport,
} from "@framework/ui/FileUpload";
import { useDevice } from "@helpdesk/shared/device";
import ShortcutKey from "@helpdesk/shared/ShortcutKey.vue";
import { __ } from "@helpdesk/shared/translation";
import LucideCircleAlert from "~icons/lucide/circle-alert";
import LucideFile from "~icons/lucide/file";
import LucidePaperclip from "~icons/lucide/paperclip";
import LucidePlus from "~icons/lucide/plus";
import LucideRotateCw from "~icons/lucide/rotate-cw";
import LucideX from "~icons/lucide/x";

// The site limit caps the whole request, so leave room for the multipart wrapping.
const MULTIPART_MARGIN = 64 * 1024;
const FILE_NAME_LIMIT = 134;

const props = defineProps<{
  modelValue: UploadResult[];
  restrictions?: Restrictions;
  transport: UploadTransport;
}>();

const emit = defineEmits<{ "update:modelValue": [UploadResult[]] }>();
const { metaIcon } = useDevice();
// The endpoint already falls back to frappe's 25 MB.
const maxFileSize = call("frappe.core.api.file.get_max_file_size").catch(
  () => 25 * 1024 * 1024
);

const uploader = useUploader({
  transport: send,
  // useUploader keeps the given object; proxy so later config applies.
  restrictions: new Proxy({}, { get: (_, key) => props.restrictions?.[key] }),
  multiple: true,
});

const accept = computed(() =>
  props.restrictions?.allowed_file_types?.join(",")
);
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

// Inputs handle their own paste; the editor takes images inline, and the rest come here.
function onPaste(event: ClipboardEvent) {
  const target = event.target as HTMLElement;
  if (target.closest("input, textarea")) return;
  const files = Array.from(event.clipboardData?.files ?? []);
  if (!target.closest("[contenteditable='true']")) {
    if (files.length) event.preventDefault();
    return add(files);
  }
  add(files.filter((file) => !file.type.startsWith("image/")));
}

onMounted(() => document.addEventListener("paste", onPaste));
onBeforeUnmount(() => document.removeEventListener("paste", onPaste));

function onDragLeave(event: DragEvent) {
  const box = event.currentTarget as HTMLElement;
  if (!box.contains(event.relatedTarget as Node)) dragging.value = false;
}

// The server fails an empty file with a bare OSError, so it never gets there.
function add(files?: FileList | File[] | null) {
  if (!files?.length) return;
  const list = Array.from(files);
  uploader.add(list.filter((file) => file.size));
  for (const file of list.filter((file) => !file.size))
    uploader.errors.value.push(
      __('"{0}" was skipped — the file is empty.', [file.name])
    );
  upload();
}

// Abort only while progress shows the body still going up. Once it is sent, or
// too small to report progress, the server may save the File: let it finish and delete it.
async function send(file: File, args, ctx) {
  const limit = await maxFileSize;
  if (ctx.signal.aborted) throw new DOMException("Cancelled", "AbortError");
  const tooLarge = __("File is larger than {0}", [formatSize(limit)]);
  if (file.size > limit - MULTIPART_MARGIN) throw new Error(tooLarge);

  const controller = new AbortController();
  let sending = false;
  ctx.signal.addEventListener("abort", () => {
    if (sending) controller.abort();
  });
  const doc: any = await props
    .transport(withShortName(file), args, {
      signal: controller.signal,
      onProgress: (loaded, total) => {
        sending = loaded < total;
        ctx.onProgress(loaded, total);
      },
    })
    .catch((error) => {
      throw error?.status === 413 ? new Error(tooLarge) : error;
    });
  if (ctx.signal.aborted)
    call("frappe.client.delete", { doctype: "File", name: doc.name }).catch(
      () => {}
    );
  return doc;
}

// File.file_name holds 140 characters, and a taken name gets a 6-character suffix;
// a longer name fails the whole upload.
function withShortName(file: File) {
  if (file.name.length <= FILE_NAME_LIMIT) return file;
  const dot = file.name.lastIndexOf(".");
  const extension = dot > 0 ? file.name.slice(dot).slice(0, 20) : "";
  const name =
    file.name.slice(0, FILE_NAME_LIMIT - extension.length) + extension;
  return new File([file], name, {
    type: file.type,
    lastModified: file.lastModified,
  });
}

// commit() skips items added mid-pass; loop until none are idle.
async function upload() {
  if (running) return;
  running = true;
  try {
    while (uploader.items.some((item) => item.status === "idle")) {
      await uploader.commit();
      emitDone();
    }
  } finally {
    // Else one throw stalls every later file.
    running = false;
  }
}

// Back to idle with the same File; the upload loop picks it up.
function retry(id: string) {
  uploader.retry(id);
  upload();
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
      .map((item) => ({
        file_url: item.fileUrl!,
        file_name: item.name,
        is_private: item.isPrivate,
      }))
  );
}

function isBusy(item: UploadItem) {
  return item.status === "idle" || item.status === "uploading";
}

function meta(item: UploadItem) {
  if (item.status === "error") return plainText(item.error);
  if (isBusy(item))
    return __("Uploading… {0}%", [Math.round(item.progress * 100)]);
  return formatSize(item.size ?? 0);
}

// Server messages carry markup, like `<strong>File Name</strong>`.
function plainText(html = "") {
  return new DOMParser().parseFromString(html, "text/html").body.textContent;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${Number((bytes / 1024 / 1024).toFixed(1))} MB`;
}

function isImage(name: string) {
  return /\.(png|jpe?g|gif|webp|svg|bmp|avif)$/i.test(name);
}
</script>
