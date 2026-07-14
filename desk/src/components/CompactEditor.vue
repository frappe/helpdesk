<template>
  <div class="flex flex-col">
    <Editor
      ref="editorRef"
      v-model="internalContent"
      :extensions="extensions"
      v-bind="uploadFn ? { uploadFunction: uploadFn } : {}"
      :placeholder="placeholder"
    >
      <template #default>
        <EditorBubbleMenu :items="commentToolbar" />
        <div
          class="flex items-center overflow-x-auto rounded-t border border-b-0 border-[--surface-gray-2] px-1 py-1"
        >
          <div
            v-if="showAttachments"
            class="inline-flex items-center gap-1.5 pe-1"
          >
            <FileUploader
              :upload-args="{ private: true }"
              @success="addAttachment"
            >
              <template #default="{ openFileSelector, uploading }">
                {{ syncUploadingState(uploading) }}
                <button
                  class="flex rounded p-1 text-ink-gray-8 transition-colors hover:bg-surface-gray-3 disabled:opacity-40"
                  :disabled="uploading"
                  @click="openFileSelector()"
                >
                  <AttachmentIcon
                    class="h-4 w-4"
                    style="stroke-width: 1.5 !important"
                  />
                </button>
              </template>
            </FileUploader>
            <div class="h-4 w-[2px] border-s" />
          </div>
          <EditorFixedMenu :items="fullToolbar" />
        </div>
        <EditorContent :class="editorClass" />
      </template>
    </Editor>
    <div
      v-if="showAttachments && attachments?.length"
      class="flex flex-wrap gap-2 mt-2"
    >
      <AttachmentItem
        v-for="attachment in attachments ?? []"
        :key="attachment.file_url"
        :label="attachment.file_name"
        :url="attachment.file_url"
      >
        <template #suffix>
          <FeatherIcon
            class="h-3.5 cursor-pointer"
            name="x"
            @click.self.stop="removeAttachment(attachment)"
          />
        </template>
      </AttachmentItem>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AttachmentItem } from "@/components";
import {
  buildEditorExtensions,
  commentToolbar,
  fullToolbar,
} from "@/components/editor/config";
import { AttachmentIcon } from "@/components/icons";
import { getUserEmailInfo } from "@/composables/useUserEmailInfo";
import { isContentEmpty } from "@/utils";
import { FeatherIcon, FileUploader, type UploadedFile } from "frappe-ui";
import {
  Editor,
  EditorBubbleMenu,
  EditorContent,
  EditorFixedMenu,
} from "frappe-ui/editor";
import { computed, nextTick, onMounted, ref, watch } from "vue";

type UploadFunction = (file: File) => Promise<UploadedFile>;

const props = withDefaults(
  defineProps<{
    placeholder?: string;
    minHeight?: string;
    maxHeight?: string;
    extensions?: any[];
    showSignature?: boolean;
    type?: "Saved Reply" | "Email";
    showAttachments?: boolean;
    uploadFn?: UploadFunction;
  }>(),
  {
    placeholder: "",
    minHeight: "min-h-[180px]",
    maxHeight: "max-h-80",
    extensions: () => [],
    showSignature: false,
    type: "Saved Reply",
    showAttachments: false,
  }
);

const internalContent = defineModel<string>({ default: "" });

const editorRef = ref<any>(null);
const attachments = defineModel<UploadedFile[] | null>("attachments", {
  default: () => [],
});
const isUploading = ref(false);

const extensions = buildEditorExtensions({ extra: props.extensions });

const savedReplyClass = [
  "!prose-sm max-w-full overflow-auto py-1.5 px-3",
  "rounded-b border border-[--surface-gray-2] bg-surface-gray-2",
  "placeholder-ink-gray-4",
  "hover:border-outline-elevation-2 hover:shadow-sm",
  "focus:bg-surface-base focus:border-outline-gray-4 focus:shadow-sm focus:ring-0",
  "focus-visible:ring-2 focus-visible:ring-outline-gray-3",
  "text-ink-gray-8 transition-colors -mt-0.5",
];

const emailClass = [
  "!prose-sm max-w-full overflow-auto py-1.5 px-3",
  "rounded-b border border-[--surface-gray-2] bg-surface-base",
  "placeholder-ink-gray-4",
  "text-ink-gray-8 transition-colors -mt-0.5",
];

const editorClass = computed(() => [
  ...(props.type === "Email" ? emailClass : savedReplyClass),
  props.minHeight,
  props.maxHeight,
]);

const userResource = getUserEmailInfo();

function getDefaultContent(signature: string): string {
  return `<p></p><p></p>${signature}`;
}

function applySignature(signature: string) {
  if (!isContentEmpty(internalContent.value)) return;
  const commands = editorRef.value?.editor?.commands;
  if (commands) {
    commands.setContent(signature);
    setTimeout(() => {
      editorRef.value?.editor?.commands?.focus("start");
    }, 0);
  } else {
    internalContent.value = signature;
  }
}

function addAttachment(file: UploadedFile) {
  attachments.value = [...(attachments.value ?? []), file];
}

function removeAttachment(attachment: UploadedFile) {
  attachments.value = (attachments.value ?? []).filter((a) => a !== attachment);
}

// FileUploader exposes `uploading` only via slot scope, so mirror it into a
// ref that the parent can read through the exposed `isUploading`.
function syncUploadingState(uploading: boolean): string {
  isUploading.value = uploading;
  return "";
}

function getContent(): string {
  return editorRef.value?.editor?.getHTML() ?? "";
}

function isEmpty(): boolean {
  return !editorRef.value?.editor?.state?.doc?.textContent?.trim()?.length;
}

function reset() {
  const commands = editorRef.value?.editor?.commands;
  if (!commands) {
    internalContent.value = "";
    return;
  }
  const data = userResource?.data as { email_signature?: string } | null;
  const sig = data?.email_signature
    ? getDefaultContent(data.email_signature)
    : "";
  commands.setContent(sig || "<p></p>");
  internalContent.value = sig;
  attachments.value = null;
  setTimeout(() => {
    editorRef.value?.editor?.commands?.focus("start");
  }, 0);
}

if (props.showSignature) {
  // Late arrival: resource resolves after mount
  watch(
    () => userResource.data,
    (data: { email_signature?: string } | null) => {
      if (!data?.email_signature) return;
      applySignature(getDefaultContent(data.email_signature));
    }
  );
}

onMounted(() => {
  if (!props.showSignature) return;

  nextTick(() => {
    const data = userResource.data as { email_signature?: string } | null;
    if (data?.email_signature) {
      applySignature(getDefaultContent(data.email_signature));
    }
  });
});

defineExpose({
  getContent,
  isEmpty,
  reset,
  editorRef,
  isUploading,
});
</script>
