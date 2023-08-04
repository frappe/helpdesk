<template>
  <div class="group flex gap-3">
    <div class="flex w-8 justify-end">
      <Avatar
        :image="user?.user_image"
        :label="user?.full_name || sender"
        size="xl"
      />
    </div>
    <div class="flex w-full flex-col gap-1">
      <div class="flex items-start justify-between">
        <div class="flex items-center">
          <div class="text-base text-gray-900">
            {{ user?.full_name || sender }}
          </div>
          <IconDot class="text-gray-600" />
          <Tooltip :text="dateExtended">
            <div class="text-xs text-gray-600">
              {{ dateDisplay }}
            </div>
          </Tooltip>
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
        <AttachmentItem
          v-for="a in attachments"
          :key="a.file_url"
          :label="a.file_name"
          :url="a.file_url"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRef } from "vue";
import { Avatar, Tooltip } from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import dayjs from "dayjs";
import { useUserStore } from "@/stores/user";
import AttachmentItem from "@/components/AttachmentItem.vue";
import IconDot from "~icons/ph/dot-bold";

interface Attachment {
  file_name: string;
  file_url: string;
}

interface P {
  content: string;
  date: string;
  sender: string;
  cc?: string;
  bcc?: string;
  attachments?: Attachment[];
}

const props = withDefaults(defineProps<P>(), {
  cc: () => "",
  bcc: () => "",
  attachments: () => [],
});

const userStore = useUserStore();
const user = userStore.getUser(props.sender);
const date = toRef(props, "date");
const dateDisplay = dayjs(date.value).fromNow();
const dateExtended = dayjs(date.value).format("dddd, MMMM D, YYYY h:mm A");

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}
</script>
