<template>
  <div class="flex flex-wrap gap-2">
    <AttachmentItem
      v-for="attachment in attachments"
      :key="attachment.file_url"
      :label="attachment.file_name"
      :url="attachment.file_url"
    >
      <template #suffix>
        <LucideX
          class="size-3.5 cursor-pointer text-ink-gray-6 transition-colors hover:text-ink-gray-9"
          @click.stop="emit('remove', attachment)"
        />
      </template>
    </AttachmentItem>
  </div>
</template>

<script setup lang="ts">
import { AttachmentItem } from "@/components";
import LucideX from "~icons/lucide/x";

interface Attachment {
  file_url: string;
  file_name: string;
}

withDefaults(defineProps<{ attachments?: Attachment[] }>(), {
  attachments: () => [],
});

const emit = defineEmits<{ remove: [attachment: Attachment] }>();
</script>
