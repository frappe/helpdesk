<template>
  <div class="group flex gap-3">
    <div class="flex w-8 justify-end">
      <Avatar :image="senderImage" :label="sender" size="xl" />
    </div>
    <div class="flex w-full flex-col gap-1">
      <div class="flex items-start justify-between">
        <div class="flex items-center">
          <div class="text-base text-gray-900">{{ sender }}</div>
          <IconDot class="text-gray-600" />
          <div class="text-sm text-gray-600">{{ dateDisplay }}</div>
        </div>
        <slot name="extra" :cc="cc" :bcc="bcc" :content="content" />
      </div>
      <div v-if="cc || bcc" class="flex gap-1 text-xs text-gray-600">
        <div class="font-medium">cc:</div>
        {{ cc }},
        <div class="font-medium">bcc:</div>
        {{ bcc }}
      </div>
      <div
        class="prose prose-img:rounded-lg prose-img:border max-w-none text-base text-gray-700"
      >
        <!-- This is vulnerable to attacks -->
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span class="prose prose-sm" v-html="sanitize(content)"></span>
      </div>
      <div class="flex flex-wrap gap-2">
        <a
          v-for="attachment in attachments"
          :key="attachment.file_url"
          :href="attachment.file_url"
          target="_blank"
        >
          <AttachmentItem :label="attachment.file_name" />
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRefs } from "vue";
import { Avatar } from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import dayjs from "dayjs";
import AttachmentItem from "@/components/AttachmentItem.vue";
import IconDot from "~icons/ph/dot-bold";

type Attachment = {
  file_name: string;
  file_url: string;
};

const props = defineProps({
  content: {
    type: String,
    required: true,
  },
  date: {
    type: String,
    required: true,
  },
  sender: {
    type: String,
    required: true,
  },
  senderImage: {
    type: String,
    required: false,
    default: "",
  },
  cc: {
    type: String,
    required: false,
    default: "",
  },
  bcc: {
    type: String,
    required: false,
    default: "",
  },
  attachments: {
    type: Array<Attachment>,
    required: false,
    default: [],
  },
});

const { content, date, sender, senderImage, cc, bcc } = toRefs(props);
const dateDisplay = dayjs(date.value).format("h:mm A");

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}
</script>
