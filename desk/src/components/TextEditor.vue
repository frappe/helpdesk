<template>
  <div class="rounded p-3 shadow w-full">
    <Editor
      ref="editorComponent"
      :extensions="extensions"
      :model-value="modelValue"
      :placeholder="placeholder"
      :autofocus="autofocus"
      :upload-function="(file: File) => uploadFunction(file)"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #default="{ editor }">
        <span class="text-base">
          <span class="flex items-center justify-between">
            <UserAvatar
              :name="authStore.userName"
              :image="authStore.userImage"
              expand
              strong
            />
            <slot name="top-right" />
          </span>
          <slot name="top-bottom" />
        </span>
        <EditorContent
          :editor="editor"
          :class="[
            'prose-f max-h-64 max-w-none overflow-auto my-4 min-h-[5rem]',
            getFontFamily(modelValue),
          ]"
        />
        <EditorBubbleMenu :editor="editor" :items="articleToolbar" />
        <div class="flex flex-col gap-2">
          <slot name="bottom-top" />
          <div
            class="flex flex-col space-y-1.5 sm:flex-row sm:items-center sm:justify-between sm:gap-2"
          >
            <div class="flex items-center min-w-0 overflow-x-auto max-w-[70%]">
              <slot name="bottom-left" />
              <EditorFixedMenu :editor="editor" :items="textEditorMenuItems" />
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <Button
                :label="__('Discard')"
                theme="gray"
                variant="subtle"
                v-if="!isContentEmpty(modelValue)"
                @click="
                  () => {
                    editor.commands.clearContent(true);
                    $emit('clear');
                  }
                "
              />
              <slot name="bottom-right" />
            </div>
          </div>
        </div>
      </template>
    </Editor>
  </div>
</template>
<script setup lang="ts">
import { UserAvatar } from "@/components";
import { textEditorMenuItems } from "@/editor-menu";
import { useAuthStore } from "@/stores/auth";
import {
  CleanStyles,
  ComponentUtils,
  HandleExcelPaste,
} from "@/tiptap-extensions";
import { getFontFamily, isContentEmpty, uploadFunction } from "@/utils";
import {
  Editor,
  EditorBubbleMenu,
  EditorContent,
  EditorFixedMenu,
  RichTextKit,
  articleToolbar,
} from "frappe-ui/editor";
import { computed, ref } from "vue";

interface P {
  modelValue: string;
  placeholder?: string;
  autofocus?: boolean;
}

interface E {
  (event: "clear"): void;
  (event: "update:modelValue", value: string): void;
}

withDefaults(defineProps<P>(), {
  autofocus: false,
});

defineEmits<E>();

const authStore = useAuthStore();
const editorComponent = ref(null);
const editor = computed(() => editorComponent.value?.editor);

const extensions = [
  RichTextKit.configure({ heading: { levels: [1, 2, 3, 4, 5, 6] } }),
  ComponentUtils,
  HandleExcelPaste,
  CleanStyles,
];

defineExpose({
  editor,
});
</script>
