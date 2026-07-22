<template>
  <div class="rounded p-3 shadow w-full">
    <Editor
      ref="inner"
      v-model="content"
      :extensions="extensions"
      :upload-function="uploadFunction"
      :autofocus="autofocus"
    >
      <template #default="{ editor, isEmpty }">
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

        <EditorBubbleMenu :items="commentToolbar" />
        <EditorContent
          :class="[
            'prose-f max-h-64 max-w-none overflow-auto my-4 min-h-[5rem]',
            getFontFamily(content),
          ]"
        />

        <div class="flex flex-col gap-2">
          <slot name="bottom-top" />
          <div
            class="flex flex-col space-y-1.5 overflow-auto sm:flex-row sm:justify-between"
          >
            <div class="flex items-center">
              <slot name="bottom-left" />
              <EditorFixedMenu :items="ticketToolbar" />
            </div>
            <div class="flex items-center gap-2">
              <Button
                label="Discard"
                theme="gray"
                variant="subtle"
                v-if="!isEmpty"
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
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { getFontFamily } from "@/utils";
import { Button } from "frappe-ui";
import {
  Editor,
  EditorBubbleMenu,
  EditorContent,
  EditorFixedMenu,
} from "frappe-ui/editor";
import { computed, ref } from "vue";
import {
  buildEditorExtensions,
  commentToolbar,
  ticketToolbar,
} from "./editor/config";

interface P {
  modelValue: string;
  autofocus?: boolean;
  uploadFunction?: (file: any) => Promise<any>;
}

interface E {
  (event: "clear"): void;
  (event: "update:modelValue", value: string): void;
}

const props = withDefaults(defineProps<P>(), {
  autofocus: false,
});

const emit = defineEmits<E>();

const authStore = useAuthStore();
const inner = ref(null);

const content = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const extensions = buildEditorExtensions();

const editor = computed(() => inner.value?.editor);

defineExpose({
  editor,
});
</script>
