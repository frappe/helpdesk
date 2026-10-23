<template>
  <!-- Width is capped here, not on the body, so the body sizes to its content. -->
  <div
    class="flex min-w-0 max-w-[80%] flex-col gap-1"
    :class="isCustomer ? 'items-end' : 'items-start'"
  >
    <div
      class="w-fit min-w-0 max-w-full break-words rounded-6 px-2.5 py-2.5 text-p-base text-ink-gray-9 shadow-[inset_0_0_0.25px_0.25px_rgba(0,0,0,0.03)]"
      :class="isCustomer ? 'bg-surface-gray-2' : 'bg-surface-gray-1'"
    >
      <PortalEmailContent v-if="hasText" :content="activity.data.content" />
      <!-- Attached images stay chips too; the chip previews them on click. -->
      <div
        v-if="attachments.length"
        class="flex flex-wrap gap-1.5"
        :class="{ 'mt-1.5': hasText }"
      >
        <AttachmentChip
          v-for="(file, index) in attachments"
          :key="`${index}:${file.file_url}`"
          :label="file.file_name"
          :url="file.file_url"
        />
      </div>
      <span v-if="isBlank" class="italic text-ink-gray-6">
        {{ __("No message") }}
      </span>
    </div>

    <!-- Sender name sits outside the body; the viewer's own messages go unnamed. -->
    <div
      class="flex max-w-full items-center gap-1 px-1 text-xs text-ink-gray-6"
    >
      <template v-if="!isViewer">
        <span class="min-w-0 truncate">{{ activity.author?.fullname }}</span>
        <span aria-hidden="true">·</span>
      </template>
      <Tooltip :text="dateFormat(activity.timestamp)">
        <time class="shrink-0" :datetime="at.format()">
          {{ at.format(DATE_FORMATS.clock) }}
        </time>
      </Tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Tooltip } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { DATE_FORMATS, isContentEmpty } from "@helpdesk/shared/utils";
import { AttachmentChip } from "@framework/ui/components/ActivityTimeline";
import { dateFormat, dayjsLocal } from "@helpdesk/shared/timezone";
import PortalEmailContent from "./PortalEmailContent.vue";

type Attachment = { file_name: string; file_url: string };

const props = defineProps<{
  activity: any;
  isCustomer: boolean;
  isViewer: boolean;
}>();

const at = computed(() => dayjsLocal(props.activity.timestamp));
const hasText = computed(() => !isContentEmpty(props.activity.data.content));

const attachments = computed<Attachment[]>(
  () => props.activity.data.attachments || []
);
const isBlank = computed(() => !hasText.value && !attachments.value.length);
</script>
