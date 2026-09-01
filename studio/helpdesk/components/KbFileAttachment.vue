<template>
  <div class="flex flex-col gap-2">
    <!-- A drop target has to look like one: a dashed edge and enough height to aim
         at, where the single-file row could pass for a text input. -->
    <button
      type="button"
      class="relative flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-outline-gray-3 bg-surface-gray-1 px-3 py-4 hover:border-outline-gray-4 hover:bg-surface-gray-2"
      :class="{ '!border-outline-gray-4 !bg-surface-gray-2': isOver }"
      @click="openFileSelector"
      @dragenter.prevent="isOver = true"
      @dragover.prevent="isOver = true"
      @dragleave.prevent="isOver = false"
      @drop.prevent="onDrop"
    >
      <FeatherIcon name="upload" class="size-4 shrink-0 text-ink-gray-5" />
      <span class="text-p-base text-ink-gray-5">
        {{
          uploading
            ? `Uploading ${pending} file${pending === 1 ? "" : "s"}…`
            : "Drop files here, or click to choose"
        }}
      </span>
      <!-- Covers the drop target so a file released anywhere on it lands on the
           input too. -->
      <input
        ref="input"
        type="file"
        multiple
        class="absolute inset-0 cursor-pointer opacity-0"
        @click.stop
        @change="onPick"
      />
    </button>

    <ul v-if="files.length" class="m-0 flex list-none flex-col gap-1 p-0">
      <li v-for="file in files" :key="file.name" class="flex min-w-0 items-center gap-1.5 rounded-md bg-surface-gray-2 px-2 py-1 text-p-sm text-ink-gray-7">
        <FeatherIcon
          name="paperclip"
          class="size-3.5 shrink-0 text-ink-gray-5"
        />
        <span class="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap">{{ file.file_name || file.name }}</span>
        <button
          type="button"
          class="grid place-items-center rounded text-ink-gray-5 hover:bg-surface-gray-3 hover:text-ink-gray-8"
          :aria-label="`Remove ${file.file_name || file.name}`"
          @click.stop="remove(file)"
        >
          <FeatherIcon name="x" class="size-3.5" />
        </button>
      </li>
    </ul>

    <p v-if="error" class="text-p-sm text-ink-red-6">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
// Attachment field for the KB new-ticket form: a drop target that takes several files at
// once, uploads each and hands the resulting File docs back to the page.
//
// Not frappe-ui's `FileUploader`: it owns a single `<input>` with no `multiple`, and one
// upload at a time — so a requester with three screenshots had to attach, wait, attach
// again. This drives the same `FileUploadHandler` it uses, once per file.

import { computed, ref } from "vue";
import { FeatherIcon, FileUploadHandler } from "frappe-ui";

// Private, and in the folder the ticket thread's own uploads go to — an attachment on a
// support ticket is not public content.
const UPLOAD_ARGS = { folder: "Home/Helpdesk", private: true };

const props = withDefaults(defineProps<{ files?: any[] }>(), {
  files: () => [],
});
const emit = defineEmits<{ "update:files": [files: any[]] }>();

const input = ref<HTMLInputElement | null>(null);
const isOver = ref(false);
const pending = ref(0);
const error = ref("");

const uploading = computed(() => pending.value > 0);

function openFileSelector() {
  input.value?.click();
}

function onPick(event: Event) {
  const picked = (event.target as HTMLInputElement).files;
  if (picked?.length) upload(Array.from(picked));
  // Cleared so picking the same file twice in a row still fires `change`.
  if (input.value) input.value.value = "";
}

function onDrop(event: DragEvent) {
  isOver.value = false;
  const dropped = event.dataTransfer?.files;
  if (dropped?.length) upload(Array.from(dropped));
}

async function upload(selected: File[]) {
  error.value = "";
  pending.value += selected.length;
  // Settled, not all: one rejected file (over the size limit, usually) must not throw away
  // the ones that uploaded beside it.
  const results = await Promise.allSettled(
    selected.map((file) => new FileUploadHandler().upload(file, UPLOAD_ARGS))
  );
  pending.value -= selected.length;

  const uploaded = results
    .filter((result) => result.status === "fulfilled")
    .map((result: any) => result.value);
  if (uploaded.length) emit("update:files", [...props.files, ...uploaded]);

  const failed = results.find((result) => result.status === "rejected") as any;
  if (failed)
    error.value = failed.reason?.message || "Some files could not be uploaded";
}

function remove(file: any) {
  emit(
    "update:files",
    props.files.filter((attached) => attached.name !== file.name)
  );
}
</script>
