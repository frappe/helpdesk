<template>
  <div class="flex flex-col divide-y rounded-b-xl">
    <div class="ml-2 flex flex-wrap gap-2 py-2">
      <AttachmentItem
        v-for="attachment in attachments"
        :key="attachment"
        :label="attachment.file_name"
      >
        <template #suffix>
          <IconX
            class="h-4 w-4 cursor-pointer"
            @click="removeAttachment(attachment)"
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
            class="h-4 w-4 text-gray-700"
            @click="isTextFormattingVisible = !isTextFormattingVisible"
          />
        </div>
        <FileUploader @success="addAttachment">
          <template #default="{ uploading, openFileSelector }">
            <div class="flex h-7 w-7 items-center justify-center">
              <IconAttachment
                class="h-4 w-4 cursor-pointer text-gray-700"
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
          class="h-4 w-4 cursor-pointer text-gray-700"
          @click.prevent="clear"
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
import IconAttachment from "~icons/lucide/paperclip";
import IconDelete from "~icons/lucide/trash-2";
import IconTextT from "~icons/lucide/type";
import IconX from "~icons/lucide/x";

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

const emit = defineEmits<{
  (event: "content-cleared"): void;
  (event: "update:attachments", data: any): void;
}>();

const { attachments, editor } = toRefs(props);
const isTextFormattingVisible = ref(false);

function addAttachment(attachment: any) {
  emit("update:attachments", [...attachments.value, attachment]);
}

function removeAttachment(attachment: any) {
  emit(
    "update:attachments",
    attachments.value.filter((a) => a.name !== attachment.name)
  );
}

function clear() {
  editor.value.commands.clearContent();
  emit("content-cleared");
}
</script>
