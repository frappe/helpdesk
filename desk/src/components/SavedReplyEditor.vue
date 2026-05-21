<template>
  <TextEditor
    ref="editorRef"
    :editor-class="editorClass"
    :bubble-menu="false"
    :content="internalContent"
    :fixed-menu="(menuButtons as any)"
    :extensions="extensions"
    v-bind="uploadFn ? { uploadFunction: uploadFn } : {}"
    :placeholder="placeholder"
    @change="(val: string) => (internalContent = val)"
  />
</template>

<script setup lang="ts">
import { menuButtons } from "@/components/Settings/SavedReplies/savedReplies";
import {
  CleanStyles,
  ComponentUtils,
  HandleExcelPaste,
} from "@/tiptap-extensions";
import { isContentEmpty, uploadFunction } from "@/utils";
import { createResource, TextEditor } from "frappe-ui";
import { computed, nextTick, onMounted, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    placeholder?: string;
    minHeight?: string;
    maxHeight?: string;
    extensions?: any[];
    showSignature?: boolean;
    doctype?: string;
    docname?: string | null;
    type?: "Saved Reply" | "Email";
  }>(),
  {
    modelValue: "",
    placeholder: "",
    minHeight: "min-h-[180px]",
    maxHeight: "max-h-80",
    extensions: () => [ComponentUtils, HandleExcelPaste, CleanStyles],
    showSignature: false,
    doctype: "HD Ticket",
    docname: null,
    type: "Saved Reply",
  }
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const editorRef = ref<any>(null);
const internalContent = ref(props.modelValue);

watch(internalContent, (val) => emit("update:modelValue", val));

watch(
  () => props.modelValue,
  (val) => {
    if (val !== internalContent.value) internalContent.value = val;
  }
);

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
const userResource = props.showSignature
  ? createResource({
      url: "helpdesk.api.auth.get_current_user_email_info",
      cache: "current-user-email-info",
      auto: true,
    })
  : null;

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

if (props.showSignature && userResource) {
  // Late arrival: resource resolves after mount
  watch(
    () => userResource.data,
    (data: { email_signature?: string } | null) => {
      if (!data?.email_signature) return;
      applySignature(`<br>${data.email_signature}`);
    }
  );

  // Early arrival: resource was already cached when component mounts
  onMounted(() => {
    nextTick(() => {
      const data = userResource.data as { email_signature?: string } | null;
      if (data?.email_signature) {
        applySignature(`<br>${data.email_signature}`);
      }
    });
  });
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
  const sig = data?.email_signature ? `<br>${data.email_signature}` : "";
  commands.setContent(sig || "<p></p>", false);
  internalContent.value = sig;
  setTimeout(() => {
    editorRef.value?.editor?.commands?.focus("start");
  }, 0);
}

defineExpose({ getContent, isEmpty, reset, editorRef });
</script>
