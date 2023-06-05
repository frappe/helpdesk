<template>
  <div
    class="rounded-xl"
    :style="{
      'box-shadow':
        '0px 0px 1px rgba(0, 0, 0, 0.45), 0px 1px 2px rgba(0, 0, 0, 0.1)',
    }"
  >
    <FTextEditor
      ref="textEditor"
      v-bind="attributes"
      editor-class="resize-y rounded-lg prose-sm max-w-none p-3 overflow-auto h-32 focus:outline-none"
      @change="emit('change', $event)"
    >
      <template #top>
        <slot name="top" />
      </template>
      <template #editor="props">
        <slot name="editor" v-bind="props" />
      </template>
      <template #bottom>
        <slot name="bottom" :editor="editor">
          <TextEditorBottom :editor="editor" />
        </slot>
      </template>
    </FTextEditor>
  </div>
</template>
<script setup lang="ts">
import { computed, ref, useAttrs } from "vue";
import { TextEditor as FTextEditor } from "frappe-ui";
import TextEditorBottom from "./TextEditorBottom.vue";

const emit = defineEmits<{
  (event: "change", value: string): void;
}>();

const attributes = useAttrs();
const textEditor = ref();
const editor = computed(() => textEditor.value?.editor);

defineExpose({
  editor,
});
</script>
