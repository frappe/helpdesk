<template>
  <div class="rounded p-3 shadow">
    <FTextEditor
      ref="e"
      v-bind="$attrs"
      editor-class="prose max-h-64 prose-sm max-w-none overflow-auto my-4 min-h-[5rem]"
      bubble-menu
      :content="modelValue"
      @change="$emit('update:modelValue', $event)"
    >
      <template #top>
        <span>
          <span class="flex items-center justify-between">
            <UserAvatar :user="authStore.userId" expand />
            <slot name="top-right" />
          </span>
          <slot name="top-bottom" />
        </span>
      </template>
      <template #bottom>
        <div class="flex flex-col gap-2">
          <slot name="bottom-top" />
          <div class="flex justify-between">
            <div class="flex items-center gap-1">
              <TextEditorFixedMenu :buttons="fixedMenu" />
              <slot name="bottom-left" />
            </div>
            <div class="flex items-center gap-2">
              <Button
                label="Discard"
                theme="gray"
                variant="subtle"
                @click="
                  () => {
                    editor.commands.clearContent();
                    $emit('clear');
                  }
                "
              >
                <template #prefix>
                  <Icon icon="lucide:trash-2" />
                </template>
              </Button>
              <slot name="bottom-right" />
            </div>
          </div>
        </div>
      </template>
    </FTextEditor>
  </div>
</template>
<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { TextEditor as FTextEditor, TextEditorFixedMenu } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useAuthStore } from "@/stores/auth";
import { UserAvatar } from "@/components";

interface P {
  modelValue: string;
  autofocus?: boolean;
}

interface E {
  (event: "clear"): void;
  (event: "update:modelValue"): string;
}

const props = withDefaults(defineProps<P>(), {
  autofocus: false,
});

defineEmits<E>();

const e = ref(null);
const editor = computed(() => e.value.editor);
const authStore = useAuthStore();
const fixedMenu = [
  "Paragraph",
  ["Heading 2", "Heading 3", "Heading 4", "Heading 5"],
  "Bullet List",
  "Numbered List",
  "Image",
  "Video",
  "Link",
  "Blockquote",
  "Code",
];

defineExpose({
  editor,
});

if (props.autofocus) {
  nextTick(() => e.value.editor.commands.focus());
}
</script>
