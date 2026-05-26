<template>
  <div class="flex flex-col">
    <TextEditor
      ref="editorRef"
      :editor-class="editorClass"
      :bubble-menu="false"
      :content="internalContent"
      :extensions="extensions"
      v-bind="uploadFn ? { uploadFunction: uploadFn } : {}"
      :placeholder="placeholder"
      @change="(val: string) => (internalContent = val)"
    >
      <template #top>
        <div
          class="flex items-center overflow-x-auto rounded-t border border-b-0 border-[--surface-gray-2] px-2 py-1"
        >
          <div
            v-if="showAttachments"
            class="inline-flex items-center gap-1.5 pr-1"
          >
            <FileUploader
              :upload-args="{ private: true }"
              @success="(f: any) => attachments.push(f)"
            >
              <template #default="{ openFileSelector, uploading }">
                {{ void (isUploading = uploading) }}
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
            <div class="h-4 w-[2px] border-l" />
          </div>
          <TextEditorFixedMenu :buttons="(menuButtons as any)" />
        </div>
      </template>
    </TextEditor>
    <div
      v-if="showAttachments && attachments.length"
      class="flex flex-wrap gap-2 mt-2"
    >
      <AttachmentItem
        v-for="attachment in attachments"
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
import { AttachmentIcon } from "@/components/icons";
import { menuButtons } from "@/components/Settings/SavedReplies/savedReplies";
import { getUserEmailInfo } from "@/composables/useUserEmailInfo";
import {
  CleanStyles,
  ComponentUtils,
  HandleExcelPaste,
} from "@/tiptap-extensions";
import { isContentEmpty, uploadFunction } from "@/utils";
import {
  FeatherIcon,
  FileUploader,
  TextEditor,
  TextEditorFixedMenu,
} from "frappe-ui";
import { computed, nextTick, onMounted, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    placeholder?: string;
    minHeight?: string;
    maxHeight?: string;
    extensions?: any[];
    showSignature?: boolean;
    doctype?: string;
    docname?: string | null;
    type?: "Saved Reply" | "Email";
    showAttachments?: boolean;
  }>(),
  {
    placeholder: "",
    minHeight: "min-h-[180px]",
    maxHeight: "max-h-80",
    extensions: () => [ComponentUtils, HandleExcelPaste, CleanStyles],
    showSignature: false,
    doctype: "HD Ticket",
    docname: null,
    type: "Saved Reply",
    showAttachments: false,
  }
);

const internalContent = defineModel<string>({ default: "" });

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const editorRef = ref<any>(null);
const attachments = ref<any[]>([]);
const isUploading = ref(false);

const savedReplyClass = [
  "!prose-sm max-w-full overflow-auto py-1.5 px-2",
  "rounded-b border border-[--surface-gray-2] bg-surface-gray-2",
  "placeholder-ink-gray-4",
  "hover:border-outline-gray-modals hover:shadow-sm",
  "focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0",
  "focus-visible:ring-2 focus-visible:ring-outline-gray-3",
  "text-ink-gray-8 transition-colors -mt-0.5",
];

const emailClass = [
  "!prose-sm max-w-full overflow-auto py-1.5 px-2",
  "rounded-b border border-[--surface-gray-2] bg-surface-white",
  "placeholder-ink-gray-4",
  "text-ink-gray-8 transition-colors -mt-0.5",
];

const editorClass = computed(() => [
  ...(props.type === "Email" ? emailClass : savedReplyClass),
  props.minHeight,
  props.maxHeight,
]);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const uploadFn = props.docname
  ? (file: any) => uploadFunction(file, props.doctype, props.docname as string)
  : null;

// ─── Signature ────────────────────────────────────────────────
const userResource = getUserEmailInfo();

function getDefaultContent(signature: string): string {
  return `<p></p><p></p><p></p><p></p><p></p>${signature}`;
}

function applySignature(signature: string) {
  if (!isContentEmpty(internalContent.value)) return;
  const commands = editorRef.value?.editor?.commands;
  if (commands) {
    commands.setContent(signature, false);
    setTimeout(() => {
      editorRef.value?.editor?.commands?.focus("start");
    }, 0);
  } else {
    internalContent.value = signature;
  }
}

// Early arrival: resource was already cached when component mounts

function removeAttachment(attachment: any) {
  attachments.value = attachments.value.filter((a) => a !== attachment);
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
  commands.setContent(sig || "<p></p>", false);
  internalContent.value = sig;
  attachments.value = [];
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
  userResource.reload();

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
  attachments,
  isUploading,
});
</script>
