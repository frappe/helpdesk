<template>
  <div class="rounded bg-gray-50 px-4 py-3 w-full">
    <TextEditor
      ref="editorRef"
      :editor-class="['prose-f shrink text-p-sm', getFontFamily(_content)]"
      :content="_content"
      :editable="editable"
      :bubble-menu="textEditorMenuButtons"
      @change="(event:string) => {_content = event}"
    >
      <template #bottom v-if="!editable">
        <div class="flex flex-row-reverse">
          <Button
            label="Edit"
            iconLeft="edit-2"
            class="text-gray-600 h-4"
            variant="subtle"
            @click="editable = !editable"
          />
        </div>
      </template>
      <template #bottom v-if="editable">
        <div class="flex flex-row-reverse gap-2">
          <Button label="Save" @click="handleSave" variant="solid" />
          <Button label="Discard" @click="handleDiscard" />
        </div>
      </template>
    </TextEditor>
  </div>
</template>

<script setup lang="ts">
import { PropType, ref } from "vue";
import { computed } from "vue";
import { TicketActivity } from "@/types";
import { textEditorMenuButtons, getFontFamily } from "@/utils";
import { TextEditor } from "frappe-ui";

const props = defineProps({
  summary: {
    type: Object as PropType<TicketActivity>,
    required: true,
  },
});

const _content = ref(props.summary.content);
const editable = ref(false);

function handleSave() {
  console.log("Save Comment");
}
function handleDiscard() {
  editable.value = false;
  _content.value = props.summary.content;
}
</script>

<style scoped></style>
