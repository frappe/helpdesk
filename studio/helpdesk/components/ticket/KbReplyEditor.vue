<template>
  <div class="kb-reply" :class="{ 'kb-reply--opening': opening }">
    <div class="kb-reply__frame">
      <Editor
        ref="editorRef"
        v-model="content"
        :extensions="extensions"
        :placeholder="placeholder"
        :upload-function="uploadFile"
        autofocus
      >
        <template #default="{ editor, isEmpty }">
          <EditorBubbleMenu :items="commentToolbar" />

          <!-- Utilities, not scoped CSS: the scope attribute never reaches the ProseMirror node. -->
          <EditorContent
            class="prose prose-sm my-2 max-h-64 min-h-[5rem] max-w-none overflow-y-auto"
          />

          <div v-if="attachments.length" class="mb-2 flex flex-wrap gap-2">
            <Button
              v-for="file in attachments"
              :key="file.file_url"
              variant="outline"
              icon-left="lucide-file"
              icon-right="lucide-x"
              :label="file.file_name"
              @click="onRemoveAttachment?.(file)"
            />
          </div>

          <div class="flex items-center justify-between gap-2">
            <div class="flex min-w-0 items-center gap-1 overflow-x-auto">
              <!-- frappe-ui's FileUploader has no `multiple`, so three files meant three trips. -->
              <input
                ref="fileInput"
                type="file"
                multiple
                class="hidden"
                @change="pickFiles"
              />
              <Button
                variant="ghost"
                icon="lucide-paperclip"
                :loading="uploading"
                aria-label="Attach files"
                @click="fileInput?.click()"
              />
              <EditorFixedMenu :items="replyToolbar" />
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <Button
                variant="ghost"
                label="Discard"
                @click="discard(editor)"
              />
              <Button
                variant="solid"
                label="Send"
                :disabled="isEmpty"
                :loading="sending"
                @click="emit('send')"
              />
            </div>
          </div>
        </template>
      </Editor>
    </div>
  </div>
</template>

<script setup lang="ts">
// The desk's own editor, so a reply serialises to the same markup. A component rather
// than Studio blocks because only the Editor's slot hands over the instance a toolbar needs.
import { computed, onMounted, ref } from "vue";
import { Button, FileUploadHandler, toast, useFileUpload } from "frappe-ui";
import {
  Blockquote,
  Bold,
  BulletList,
  Editor,
  EditorBubbleMenu,
  EditorContent,
  EditorFixedMenu,
  HeadingGroup,
  InlineCode,
  InsertImage,
  InsertLink,
  InsertVideo,
  Italic,
  OrderedList,
  Paragraph,
  RichTextKit,
  Separator,
  commentToolbar,
  type CommandMenuItem,
  type MenuItem,
} from "frappe-ui/editor";

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    attachments?: any[];
    sending?: boolean;
    placeholder?: string;
    // Where an inline upload is filed, so a pasted image belongs to the ticket.
    doctype?: string;
    docname?: string;
    uploadArgs?: Record<string, unknown>;
    onAttach?: (file: any) => void;
    onRemoveAttachment?: (file: any) => void;
  }>(),
  {
    modelValue: "",
    attachments: () => [],
    sending: false,
    placeholder: "Type a message",
    doctype: "HD Ticket",
    uploadArgs: () => ({ folder: "Home/Helpdesk", private: true }),
  }
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
  send: [];
  discard: [];
}>();

const OPEN_MS = 180;

// Clipped only while growing: the clipping a height animation needs would cut off the menus.
const opening = ref(true);
onMounted(() => setTimeout(() => (opening.value = false), OPEN_MS));

const editorRef = ref<InstanceType<typeof Editor> | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const pending = ref(0);
const uploading = computed(() => pending.value > 0);

const content = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

// The desk's `buildEditorExtensions()`, less the mention list and its local paste helpers.
const extensions = [
  RichTextKit.configure({ heading: { levels: [2, 3, 4, 5, 6] } }),
];

// The desk's, less the `cleanStyles` command that comes from its own extension.
const ClearFormatting: CommandMenuItem = {
  label: "Clear formatting",
  icon: "lucide-brush-cleaning",
  action: (editor) => editor.chain().focus().unsetAllMarks().clearNodes().run(),
};

// The desk's `ticketToolbar`, item for item.
const replyToolbar: MenuItem[] = [
  Paragraph,
  HeadingGroup,
  Separator,
  Bold,
  Italic,
  Separator,
  BulletList,
  OrderedList,
  Separator,
  InsertImage,
  InsertVideo,
  InsertLink,
  Blockquote,
  InlineCode,
  ClearFormatting,
];

// Private, so the same permissions guard an upload as guard the ticket.
function uploadFile(file: File) {
  return useFileUpload().upload(file, {
    private: true,
    doctype: props.doctype,
    docname: props.docname,
  });
}

// `allSettled`, so one file over the size limit does not throw away the ones beside it.
async function pickFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  const picked = Array.from(input.files || []);
  // Cleared so picking the same file twice in a row still fires `change`.
  input.value = "";
  if (!picked.length) return;

  pending.value += picked.length;
  const results = await Promise.allSettled(
    picked.map((file) => new FileUploadHandler().upload(file, props.uploadArgs))
  );
  pending.value -= picked.length;

  results.forEach((result) => {
    if (result.status === "fulfilled") props.onAttach?.(result.value);
  });
  if (results.some((result) => result.status === "rejected")) {
    toast.error(
      picked.length > 1
        ? "Some files could not be uploaded"
        : "Error uploading file"
    );
  }
}

function discard(editor: any) {
  editor?.commands.clearContent(true);
  emit("discard");
}

defineExpose({ editor: computed(() => editorRef.value?.editor) });
</script>

<style scoped>
/* A grid row grows from nothing to its content's size, where an `auto` height cannot. */
.kb-reply--opening {
  display: grid;
  grid-template-rows: 0fr;
  animation: kb-reply-open 180ms ease-out forwards;
}

.kb-reply--opening .kb-reply__frame {
  overflow: hidden;
  min-height: 0;
}

@keyframes kb-reply-open {
  from {
    grid-template-rows: 0fr;
    opacity: 0.5;
  }
  to {
    grid-template-rows: 1fr;
    opacity: 1;
  }
}
</style>
