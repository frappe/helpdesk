<template>
  <div class="px-5 py-3">
    <div class="mb-4 flex items-center justify-between text-base">
      <div class="flex items-center gap-0.5">
        <UserAvatar v-bind="user" size="lg" expand strong />
        <LucideDot class="h-4 w-4 text-gray-500" />
        <Tooltip :text="dayjs(date).long()">
          <div class="text-gray-600">
            {{ dayjs(date).fromNow() }}
          </div>
        </Tooltip>
      </div>
      <slot name="top-right" v-bind="{ message: content }" />
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <span class="prose-f" v-html="sanitize(content)"></span>
    <div v-if="attachments.length" class="flex flex-wrap gap-2">
      <AttachmentItem
        v-for="a in attachments"
        :key="a.file_url"
        :label="a.file_name"
        :url="a.file_url"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Tooltip } from 'frappe-ui';
import sanitizeHtml from 'sanitize-html';
import { dayjs } from '@/dayjs';
import { AttachmentItem, UserAvatar } from '@/components';
import { UserInfo } from '@/types';

interface Attachment {
  file_name: string;
  file_url: string;
}

withDefaults(
  defineProps<{
    content: string;
    date: string;
    user: UserInfo;
    cc?: string;
    bcc?: string;
    attachments?: Attachment[];
  }>(),
  {
    cc: () => '',
    bcc: () => '',
    attachments: () => [],
  }
);

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(['img']),
  });
}
</script>
