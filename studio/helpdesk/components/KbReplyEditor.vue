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

          <!-- Sized inline, not in the stylesheet: the class lands on the ProseMirror node
           but the scope attribute does not, so a scoped rule never matches it. Same
           numbers the desk uses — `max-h-64 my-4 min-h-[5rem]`. -->
          <EditorContent
            class="kb-reply__content prose prose-sm"
            :style="{
              maxHeight: '16rem',
              minHeight: '5rem',
              maxWidth: 'none',
              overflowY: 'auto',
              margin: '8px 0',
            }"
          />

          <div v-if="attachments.length" class="kb-reply__files">
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

          <div class="kb-reply__bar">
            <div class="kb-reply__tools">
              <!-- Own input rather than frappe-ui's FileUploader: that one holds a single
               `<input>` with no `multiple`, so three screenshots meant three trips. -->
              <input
                ref="fileInput"
                type="file"
                multiple
                class="kb-reply__input"
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

            <div class="kb-reply__actions">
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
// The reply composer, built from the same editor the agent portal gives its own users:
// `desk/src/components/TextEditor.vue` and the toolbar in `desk/src/components/editor/
// config.ts`. Same `frappe-ui/editor` Editor, same RichTextKit, same toolbar order and
// the same bubble menu on a selection — so a reply written here serialises to the markup
// the desk writes, and renders back the same way in the thread.
//
// It is a component rather than Studio blocks because a toolbar has to reach the editor
// instance, and only the Editor's own slot hands that over.
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
    /** Where an inline upload is filed, so a pasted image belongs to the ticket. */
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

/** How long the composer takes to grow into place. Long enough to read as a movement,
 *  short enough that the cursor is there before anyone starts typing. */
const OPEN_MS = 180;

// The composer replaces a one-line prompt, so it arrives some 160px taller than what it
// replaced and everything above it jumped. It grows into that height instead — and only
// while it is growing, because the clipping that makes a height animation possible would
// otherwise cut off the toolbar's own menus.
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

// The desk's `buildEditorExtensions()` without its mention list — a customer has no
// agents to mention — and without the desk-local paste helpers, which live in that app.
const extensions = [
  RichTextKit.configure({ heading: { levels: [2, 3, 4, 5, 6] } }),
];

/** `ClearFormatting` from the desk's config, less the `cleanStyles` command that comes
 *  from its own extension. */
const ClearFormatting: CommandMenuItem = {
  label: "Clear formatting",
  icon: "lucide-brush-cleaning",
  action: (editor) => editor.chain().focus().unsetAllMarks().clearNodes().run(),
};

/** The desk's `ticketToolbar`, item for item. */
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

/** Pasted and dropped media, filed against the ticket the way `uploadFunction` files it
 *  in the desk — private, so the same permissions guard it as the ticket. */
function uploadFile(file: File) {
  return useFileUpload().upload(file, {
    private: true,
    doctype: props.doctype,
    docname: props.docname,
  });
}

/** Everything the reader picked, uploaded together — `allSettled` so one file over the
 *  size limit does not throw away the ones beside it. */
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
/* A height animation without knowing the height: a grid row grows from nothing to its
   content's size, which is interpolable where an `auto` height is not. */
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

.kb-reply__input {
  display: none;
}

.kb-reply__files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.kb-reply__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

/* The toolbar sits beside the attach button, as it does in the desk — one row of tools
   under the message rather than a strip boxed in above it. */
.kb-reply__tools {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  overflow-x: auto;
}

.kb-reply__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
</style>
