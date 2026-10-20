<template>
  <!-- Width is capped here, not on the body, so the body sizes to its content. -->
  <div
    class="flex min-w-0 max-w-[80%] flex-col gap-1"
    :class="isCustomer ? 'items-end' : 'items-start'"
  >
    <div
      class="w-fit min-w-0 max-w-full break-words rounded-6 px-2.5 py-1.5 text-p-base text-ink-gray-9 shadow-[inset_0_0_0.25px_0.25px_rgba(0,0,0,0.03)]"
      :class="isCustomer ? 'bg-surface-gray-2' : 'bg-surface-gray-1'"
    >
      <PortalEmailContent v-if="hasText" :content="activity.data.content" />
      <!-- Images fill the bubble; the link opens the uncropped file. -->
      <div
        v-if="images.length"
        class="grid gap-1.5"
        :class="[images.length > 1 && 'grid-cols-2', { 'mt-1.5': hasText }]"
      >
        <a
          v-for="(image, index) in images"
          :key="`${index}:${image.file_url}`"
          :href="image.file_url"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img
            :src="image.file_url"
            :alt="image.file_name"
            class="block w-full rounded-4 object-cover"
            :class="images.length > 1 ? 'aspect-square' : 'max-h-72'"
            @error="failed.add(image.file_url)"
          />
        </a>
      </div>
      <div
        v-if="files.length"
        class="flex flex-wrap gap-1.5"
        :class="{ 'mt-1.5': hasText || images.length }"
      >
        <AttachmentChip
          v-for="(file, index) in files"
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
import { computed, reactive } from "vue";
import { Tooltip, dayjsLocal } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { DATE_FORMATS, isContentEmpty } from "@helpdesk/shared/utils";
import { AttachmentChip } from "@framework/ui/components/ActivityTimeline";
import { dateFormat } from "@framework/ui/components/ActivityTimeline/utils";
import PortalEmailContent from "./PortalEmailContent.vue";

type Attachment = { file_name: string; file_url: string };

const IMAGE = /\.(png|jpe?g|gif|webp|avif|svg)$/i;

const props = defineProps<{
  activity: any;
  isCustomer: boolean;
  isViewer: boolean;
}>();

const at = computed(() => dayjsLocal(props.activity.timestamp));
const hasText = computed(() => !isContentEmpty(props.activity.data.content));

// An image that fails to load, a private file say, falls back to a chip.
const failed = reactive(new Set<string>());
const attachments = computed<Attachment[]>(
  () => props.activity.data.attachments || []
);
const images = computed(() =>
  attachments.value.filter(
    (file) => IMAGE.test(file.file_url) && !failed.has(file.file_url)
  )
);
const files = computed(() =>
  attachments.value.filter((file) => !images.value.includes(file))
);
const isBlank = computed(() => !hasText.value && !attachments.value.length);
</script>
