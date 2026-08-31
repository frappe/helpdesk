<template>
  <div class="kb-attach">
    <button
      type="button"
      class="kb-attach__drop"
      :class="{ 'kb-attach__drop--over': isOver }"
      @click="openFileSelector"
      @dragenter.prevent="isOver = true"
      @dragover.prevent="isOver = true"
      @dragleave.prevent="isOver = false"
      @drop.prevent="onDrop"
    >
      <FeatherIcon name="upload" class="size-4 shrink-0 text-ink-gray-5" />
      <span class="kb-attach__hint">
        {{
          uploading
            ? `Uploading ${pending} file${pending === 1 ? "" : "s"}…`
            : "Drop files here, or click to choose"
        }}
      </span>
      <input
        ref="input"
        type="file"
        multiple
        class="kb-attach__input"
        @click.stop
        @change="onPick"
      />
    </button>

    <ul v-if="files.length" class="kb-attach__list">
      <li v-for="file in files" :key="file.name" class="kb-attach__file">
        <FeatherIcon
          name="paperclip"
          class="size-3.5 shrink-0 text-ink-gray-5"
        />
        <span class="kb-attach__name">{{ file.file_name || file.name }}</span>
        <button
          type="button"
          class="kb-attach__remove"
          :aria-label="`Remove ${file.file_name || file.name}`"
          @click.stop="remove(file)"
        >
          <FeatherIcon name="x" class="size-3.5" />
        </button>
      </li>
    </ul>

    <p v-if="error" class="kb-attach__error">{{ error }}</p>
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

<style scoped>
.kb-attach {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* A drop target has to look like one: a dashed edge and enough height to aim at, where the
   single-file row could pass for a text input. */
.kb-attach__drop {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 16px 12px;
  border: 1px dashed var(--outline-gray-3);
  border-radius: 8px;
  background: var(--surface-gray-1);
  cursor: pointer;
}

.kb-attach__drop:hover,
.kb-attach__drop--over {
  border-color: var(--outline-gray-4);
  background: var(--surface-gray-2);
}

.kb-attach__hint {
  font-size: 14px;
  line-height: 20px;
  color: var(--ink-gray-5);
}

/* Covers the drop target so a file released anywhere on it lands on the input too. */
.kb-attach__input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.kb-attach__list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.kb-attach__file {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 4px 8px;
  border-radius: 6px;
  background: var(--surface-gray-2);
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-gray-7);
}

.kb-attach__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-attach__remove {
  display: grid;
  place-items: center;
  border-radius: 4px;
  color: var(--ink-gray-5);
}

.kb-attach__remove:hover {
  background: var(--surface-gray-3);
  color: var(--ink-gray-8);
}

.kb-attach__error {
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-red-6);
}
</style>
