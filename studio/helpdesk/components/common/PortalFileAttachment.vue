<template>
  <div class="flex flex-col gap-2">
    <!-- A drop target has to look like one, where a single-file row reads as an input. -->
    <button
      type="button"
      class="relative flex w-full cursor-pointer items-center justify-center gap-2 rounded-6 border border-dashed border-outline-gray-3 bg-surface-gray-1 px-3 py-4 hover:border-outline-gray-4 hover:bg-surface-gray-2"
      :class="{ '!border-outline-gray-4 !bg-surface-gray-2': isDragOver }"
      @click="openFileSelector"
      @dragenter.prevent="isDragOver = true"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
      @drop.prevent="onDrop"
    >
      <Icon icon="lucide-upload" class="size-4 shrink-0 text-ink-gray-5" />
      <span class="text-p-base text-ink-gray-5">
        {{
          pendingUploadCount
            ? countLabel(
                pendingUploadCount,
                "Uploading 1 file…",
                "Uploading {0} files…"
              )
            : __("Drop files here, or click to choose")
        }}
      </span>
      <!-- Covers the target, so a file released anywhere on it lands on the input. -->
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
      <li
        v-for="file in files"
        :key="file.name"
        class="flex min-w-0 items-center gap-1.5 rounded-5 bg-surface-gray-2 px-2 py-1 text-p-sm text-ink-gray-7"
      >
        <Icon
          icon="lucide-paperclip"
          class="size-3.5 shrink-0 text-ink-gray-5"
        />
        <span class="min-w-0 flex-1 truncate">{{
          file.file_name || file.name
        }}</span>
        <button
          type="button"
          class="grid place-items-center rounded-4 text-ink-gray-5 hover:bg-surface-gray-3 hover:text-ink-gray-8"
          :aria-label="__('Remove {0}', [file.file_name || file.name])"
          @click.stop="remove(file)"
        >
          <Icon icon="lucide-x" class="size-3.5" />
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
// Not frappe-ui's `FileUploader`: that has no `multiple` and uploads one at a time.
import { ref } from "vue";
import { Icon } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { countLabel, uploadFiles } from "@app/utils";

const files = defineModel<any[]>("files", { default: () => [] });

const input = ref<HTMLInputElement | null>(null);
const isDragOver = ref(false);
const pendingUploadCount = ref(0);

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
  isDragOver.value = false;
  const dropped = event.dataTransfer?.files;
  if (dropped?.length) upload(Array.from(dropped));
}

async function upload(selected: File[]) {
  pendingUploadCount.value += selected.length;
  const uploaded = await uploadFiles(selected);
  pendingUploadCount.value -= selected.length;
  if (uploaded.length) files.value = [...files.value, ...uploaded];
}

function remove(file: any) {
  files.value = files.value.filter((attached) => attached.name !== file.name);
}
</script>
