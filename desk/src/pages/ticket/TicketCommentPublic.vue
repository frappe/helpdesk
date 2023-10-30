<template>
  <div class="mx-3 pt-6">
    <div class="mb-4 flex items-center justify-between text-base">
      <div class="flex items-center gap-0.5">
        <UserAvatar v-bind="user" size="lg" expand strong />
        <Icon icon="lucide:dot" class="text-gray-500" />
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
    <div class="flex flex-wrap gap-2">
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
import { Tooltip } from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { Icon } from "@iconify/vue";
import { dayjs } from "@/dayjs";
import { UserInfo } from "@/types";
import { AttachmentItem, UserAvatar } from "@/components";

interface Attachment {
  file_name: string;
  file_url: string;
}

interface P {
  content: string;
  date: string;
  user: UserInfo;
  cc?: string;
  bcc?: string;
  attachments?: Attachment[];
}

withDefaults(defineProps<P>(), {
  cc: () => "",
  bcc: () => "",
  attachments: () => [],
});

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}
</script>
