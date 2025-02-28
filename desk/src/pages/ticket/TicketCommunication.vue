<template>
  <div class="border rounded flex-1 px-3 pt-2.5 shadow bg-white">
    <div class="mb-4 flex items-center justify-between text-base">
      <div class="flex items-center gap-0.5">
        <UserAvatar v-bind="user" size="lg" expand strong :hide-avatar="true" />
        <Icon icon="lucide:dot" class="text-gray-500" />
        <Tooltip :text="dayjs(date).long()">
          <span class="text-gray-600">
            {{ dayjs.tz(date).fromNow() }}
          </span>
        </Tooltip>
      </div>
    </div>

    <EmailContent :content="sanitize(content)" />
    <div class="flex flex-wrap gap-2 mb-2">
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
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img", "video"]),
    allowedAttributes: {
      a: ["href"],
      video: ["src", "controls"],
      img: ["src"],
    },
  });
}
</script>
