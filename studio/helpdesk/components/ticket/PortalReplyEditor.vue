<template>
  <!-- A grid row grows from nothing to its content's size, where an `auto` height cannot. -->
  <div
    :class="[
      isOpening &&
        'grid transition-[grid-template-rows,opacity] duration-[180ms] ease-out motion-reduce:transition-none',
      isOpening && !hasStartedOpening && 'grid-rows-[0fr] opacity-50',
      isOpening && hasStartedOpening && 'grid-rows-[1fr]',
    ]"
  >
    <div :class="isOpening && 'min-h-0 overflow-hidden'">
      <Editor
        v-model="content"
        :extensions="extensions"
        :placeholder="placeholder"
        :upload-function="uploadInlineFile"
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
              @click="emit('removeAttachment', file)"
            />
          </div>

          <div class="flex items-center justify-between gap-2">
            <div class="flex min-w-0 items-center gap-1 overflow-x-auto">
              <input
                ref="fileInput"
                type="file"
                multiple
                class="hidden"
                @change="onFilesPicked"
              />
              <Button
                variant="ghost"
                icon="lucide-paperclip"
                :loading="pendingUploadCount > 0"
                :aria-label="__('Attach files')"
                @click="fileInput?.click()"
              />
              <EditorFixedMenu :items="replyToolbar" />
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <Button
                variant="ghost"
                :label="__('Discard')"
                @click="discard(editor)"
              />
              <Button
                variant="solid"
                :label="__('Send')"
                :disabled="isEmpty"
                :loading="isSending"
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
// The desk's editor, so a reply serialises to the same markup.
import { onMounted, ref } from "vue";
import { Button, useFileUpload } from "frappe-ui";
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
import { __ } from "@helpdesk/shared/translation";
import { uploadFiles } from "@app/utils";

const DOCTYPE = "HD Ticket";
const OPEN_MS = 180;

const props = withDefaults(
  defineProps<{
    attachments?: any[];
    isSending?: boolean;
    placeholder?: string;
    docname?: string;
  }>(),
  {
    attachments: () => [],
    isSending: false,
    placeholder: "Type a message",
  }
);

const emit = defineEmits<{
  send: [];
  discard: [];
  attach: [file: any];
  removeAttachment: [file: any];
}>();

const content = defineModel<string>({ default: "" });

// Clipped only while growing: the clipping a height animation needs would cut off the menus.
const isOpening = ref(true);
// Flipped a frame after mount, so the transition has a start state to leave.
const hasStartedOpening = ref(false);
onMounted(() => {
  requestAnimationFrame(() => (hasStartedOpening.value = true));
  setTimeout(() => (isOpening.value = false), OPEN_MS);
});

const fileInput = ref<HTMLInputElement | null>(null);
const pendingUploadCount = ref(0);

const extensions = [
  RichTextKit.configure({ heading: { levels: [2, 3, 4, 5, 6] } }),
];

// The desk's, minus `cleanStyles`, which needs its extension.
const ClearFormatting: CommandMenuItem = {
  label: "Clear formatting",
  icon: "lucide-brush-cleaning",
  action: (editor) => editor.chain().focus().unsetAllMarks().clearNodes().run(),
};

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

function uploadInlineFile(file: File) {
  return useFileUpload().upload(file, {
    private: true,
    doctype: DOCTYPE,
    docname: props.docname,
  });
}

async function onFilesPicked(event: Event) {
  const input = event.target as HTMLInputElement;
  const picked = Array.from(input.files || []);
  input.value = "";
  if (!picked.length) return;

  pendingUploadCount.value += picked.length;
  const uploaded = await uploadFiles(picked);
  pendingUploadCount.value -= picked.length;
  uploaded.forEach((file) => emit("attach", file));
}

function discard(editor: any) {
  editor?.commands.clearContent(true);
  emit("discard");
}
</script>
