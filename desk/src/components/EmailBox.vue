<template>
  <div
    class="grow cursor-pointer rounded-md border-transparent bg-gray-50 text-base leading-6 transition-all duration-300 ease-in-out"
  >
    <div class="mb-1 flex items-center justify-between gap-2">
      <!-- comment design for mobile -->
      <div v-if="isMobileView" class="flex items-center gap-2">
        <UserAvatar :name="sender.name" size="lg" />
        <div class="leading-tight">
          <span>{{ sender.full_name }}</span>
          <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
            <div class="text-xs text-gray-600">
              {{ timeAgo(creation) }}
            </div>
          </Tooltip>
        </div>
      </div>
      <!-- comment design for desktop -->
      <div v-else class="flex items-center gap-2">
        <UserAvatar :name="sender.name" size="md" />
        <span>{{ sender.full_name }}</span>
        <span>&middot;</span>
        <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
          <div class="text-sm text-gray-600">
            {{ timeAgo(creation) }}
          </div>
        </Tooltip>
      </div>

      <div class="flex gap-0.5">
        <Button
          variant="ghost"
          class="text-gray-700"
          @click="
            emit('reply', {
              content: content,
              to: sender.name,
            })
          "
        >
          <ReplyIcon class="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          class="text-gray-700"
          @click="
            emit('reply', {
              content: content,
              to: to ?? sender.name,
              cc: cc,
              bcc: bcc,
            })
          "
        >
          <ReplyAllIcon class="h-4 w-4" />
        </Button>
      </div>
    </div>
    <div class="text-sm leading-5 text-gray-600">
      {{ subject }}
    </div>
    <div class="mb-3 text-sm leading-5 text-gray-600">
      <span v-if="to" class="text-2xs mr-1 font-bold text-gray-500">TO:</span>
      <span v-if="to"> {{ to }} </span>
      <span v-if="cc">, </span>
      <span v-if="cc" class="text-2xs mr-1 font-bold text-gray-500"> CC: </span>
      <span v-if="cc">{{ cc }}</span>
      <span v-if="bcc">, </span>
      <span v-if="bcc" class="text-2xs mr-1 font-bold text-gray-500">
        BCC:
      </span>
      <span v-if="bcc">{{ bcc }}</span>
    </div>
    <div
      class="email-content prose-f max-h-[500px] overflow-y-auto"
      v-html="content"
    />
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
import { UserAvatar, AttachmentItem } from "@/components";
import { dateFormat, timeAgo, dateTooltipFormat } from "@/utils";
import { ReplyIcon, ReplyAllIcon } from "./icons/";
import { useScreenSize } from "@/composables/screen";

const props = defineProps({
  sender: {
    type: Object,
    required: true,
  },
  to: { type: String, default: null },
  cc: { type: String, default: null },
  bcc: { type: String, default: null },
  creation: { type: String, required: true },
  subject: {
    type: String,
    required: true,
  },
  attachments: {
    type: Array,
    default: () => [],
  },
  content: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["reply"]);

const { isMobileView } = useScreenSize();
</script>
