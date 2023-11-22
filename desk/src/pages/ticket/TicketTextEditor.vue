<template>
  <HTextEditor
    ref="e"
    :model-value="content"
    :placeholder="placeholder"
    @update:model-value="$emit('update:content', $event)"
    @clear="() => $emit('update:attachments', [])"
  >
    <template #bottom-top>
      <div class="flex flex-wrap gap-2">
        <AttachmentItem
          v-for="a in attachments"
          :key="a.file_url"
          :label="a.file_name"
        >
          <template #suffix>
            <Icon
              icon="lucide:x"
              @click.stop="
                $emit(
                  'update:attachments',
                  attachments.filter((a) => a.file_url !== a.file_url)
                )
              "
            />
          </template>
        </AttachmentItem>
      </div>
    </template>
    <template #bottom-left>
      <span class="flex">
        <slot name="bottom-left" />
        <FileUploader
          :upload-args="{
            doctype: 'HD Comment',
            folder: 'Home/Helpdesk',
            private: true,
          }"
          @success="(f: File) => $emit('update:attachments', [...attachments, f])"
        >
          <template #default="{ openFileSelector }">
            <Button theme="gray" variant="ghost" @click="openFileSelector()">
              <template #icon>
                <Icon icon="lucide:paperclip" />
              </template>
            </Button>
          </template>
        </FileUploader>
      </span>
    </template>
    <template #top-right>
      <slot name="top-right" />
    </template>
    <template #top-bottom>
      <slot name="top-bottom" />
    </template>
    <template #bottom-right>
      <slot name="bottom-right" />
    </template>
  </HTextEditor>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { FileUploader } from 'frappe-ui';
import { Icon } from '@iconify/vue';
import { AttachmentItem, TextEditor as HTextEditor } from '@/components';
import { File } from '@/types';

withDefaults(
  defineProps<{
    content: string;
    placeholder: string;
    attachments: File[];
    expand?: boolean;
  }>(),
  {
    expand: false,
  }
);
defineEmits<{
  (event: 'update:content', content: string): void;
  (event: 'update:attachments', attachments: File[]): void;
  (event: 'update:expand', expand: boolean): void;
}>();
const e = ref(null);
const editor = computed(() => e.value.editor);
defineExpose({
  editor,
});
</script>
