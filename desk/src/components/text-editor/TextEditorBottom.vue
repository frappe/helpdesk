<template>
  <div class="flex flex-col divide-y rounded-b-xl">
    <div class="ml-2 flex flex-wrap gap-2 py-2">
      <AttachmentItem
        v-for="attachment in attachments"
        :key="attachment"
        :label="attachment.file_name"
      >
        <template #extra>
          <IconX
            class="h-4 w-4 cursor-pointer"
            @click="emit('attachment-removed', attachment)"
          />
        </template>
      </AttachmentItem>
    </div>
    <div v-if="isTextFormattingVisible" class="px-3.5 py-2">
      <TextEditorFixedMenu />
    </div>
    <div class="flex justify-between px-3.5 py-2">
      <div class="flex items-center gap-1">
        <div
          class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg"
          :class="{
            'bg-gray-200': isTextFormattingVisible,
          }"
        >
          <IconTextT
            class="h-5 w-5 text-gray-900"
            @click="isTextFormattingVisible = !isTextFormattingVisible"
          />
        </div>
        <FileUploader @success="(file) => emit('attachment-added', file)">
          <template #default="{ uploading, openFileSelector }">
            <div class="flex h-7 w-7 items-center justify-center">
              <IconAttachment
                class="h-5 w-5 cursor-pointer text-gray-900"
                :class="{
                  'text-gray-600': uploading,
                }"
                @click="!uploading && openFileSelector()"
              />
            </div>
          </template>
        </FileUploader>
        <slot name="actions-left" />
      </div>
      <div class="flex items-center gap-4">
        <IconDelete
          class="h-5 w-5 cursor-pointer text-gray-900"
          @click.prevent="editor.commands.clearContent()"
        />
        <slot name="actions-right" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs } from "vue";
import { FileUploader } from "frappe-ui";
import TextEditorFixedMenu from "./TextEditorFixedMenu.vue";
import AttachmentItem from "@/components/AttachmentItem.vue";
import IconDelete from "~icons/espresso/delete";
import IconX from "~icons/ph/x";
import IconTextT from "~icons/ph/text-t";
import IconAttachment from "~icons/espresso/attachment";

const props = defineProps({
  editor: {
    type: Object,
    required: true,
  },
  attachments: {
    type: Array<any>,
    required: false,
    default: () => [],
  },
});

const { editor } = toRefs(props);

const emit = defineEmits<{
  (event: "attachment-added", data: any): void;
  (event: "attachment-removed", data: any): void;
  (event: "content-cleared"): void;
}>();

const isTextFormattingVisible = ref(false);
</script>
