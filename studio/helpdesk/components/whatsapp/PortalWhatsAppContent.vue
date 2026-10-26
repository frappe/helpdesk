<!-- eslint-disable vue/no-v-html -->
<template>
  <div class="flex min-w-0 flex-col gap-1.5">
    <blockquote
      v-if="message.reply_to"
      class="line-clamp-3 border-l-2 border-outline-gray-3 pl-2 text-p-sm text-ink-gray-6"
      v-html="formatWhatsAppText(message.reply_message) || __('Attachment')"
    />
    <p v-if="message.header" class="font-semibold">{{ message.header }}</p>
    <template v-if="mediaUrl">
      <a
        v-if="kind === 'image'"
        :href="mediaUrl"
        target="_blank"
        rel="noopener"
      >
        <img
          :src="mediaUrl"
          :alt="__('Image')"
          class="max-h-60 max-w-full rounded-4 object-contain"
        />
      </a>
      <video
        v-else-if="kind === 'video'"
        :src="mediaUrl"
        controls
        class="max-h-60 max-w-full rounded-4"
      />
      <audio
        v-else-if="kind === 'audio'"
        :src="mediaUrl"
        controls
        class="max-w-full"
      />
      <AttachmentChip v-else :label="fileName" :url="mediaUrl" />
    </template>
    <span v-if="placeholder" class="italic text-ink-gray-6">
      {{ placeholder }}
    </span>
    <p v-if="body" v-html="formatWhatsAppText(body)" />
    <p v-if="message.footer" class="text-p-sm text-ink-gray-6">
      {{ message.footer }}
    </p>
    <!-- Read-only here: the customer presses them on WhatsApp. -->
    <ul
      v-if="message.buttons?.length"
      class="-mx-2.5 -mb-2.5 mt-1 divide-y divide-outline-gray-2 border-t border-outline-gray-2"
      :aria-label="__('Reply buttons')"
    >
      <li
        v-for="button in message.buttons"
        :key="button.button_text"
        class="flex items-center justify-center gap-1.5 px-2.5 py-2 text-ink-gray-7"
      >
        <component
          :is="BUTTON_ICONS[button.button_type] || LucideReply"
          class="size-4 shrink-0"
          aria-hidden="true"
        />
        {{ button.button_text }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { __ } from "@helpdesk/shared/translation";
import { formatWhatsAppText } from "@helpdesk/shared/whatsapp/format";
import { AttachmentChip } from "@framework/ui/components/ActivityTimeline";
import LucideExternalLink from "~icons/lucide/external-link";
import LucidePhone from "~icons/lucide/phone";
import LucideReply from "~icons/lucide/reply";

/** A row of the whatsapp app's get_messages, as the portal reads it. */
type WhatsAppMessage = {
  direction?: "Incoming" | "Outgoing";
  message?: string;
  mime_type?: string;
  media_url?: string;
  file_name?: string;
  is_template?: boolean;
  template?: string;
  header?: string;
  footer?: string;
  reply_to?: string;
  reply_message?: string;
  buttons?: { button_text: string; button_type?: string }[];
};

const BUTTON_ICONS = {
  URL: LucideExternalLink,
  "Phone Number": LucidePhone,
  "Voice Call": LucidePhone,
};

const props = defineProps<{ message: WhatsAppMessage }>();

// Incoming media keeps only its type, so it is named rather than shown.
const MEDIA_LABELS: Record<string, string> = {
  image: __("Photo"),
  video: __("Video"),
  audio: __("Voice message"),
};

const kind = computed(() => {
  const type = props.message.mime_type?.split("/")[0];
  if (!type) return "text";
  return MEDIA_LABELS[type] ? type : "document";
});

const body = computed(
  () =>
    (props.message.is_template && props.message.template) ||
    props.message.message ||
    ""
);

// Incoming media_url is the file name the sender chose, so only our own uploads link.
const mediaUrl = computed(() =>
  props.message.direction === "Outgoing" &&
  /^\/(private\/)?files\//.test(props.message.media_url || "")
    ? props.message.media_url
    : ""
);

const fileName = computed(
  () =>
    props.message.file_name ||
    (mediaUrl.value ? mediaUrl.value.split("/").pop() : props.message.media_url) ||
    __("Document")
);

const placeholder = computed(() => {
  if (kind.value === "text") return body.value ? "" : __("Unsupported message");
  if (mediaUrl.value) return "";
  return kind.value === "document" ? fileName.value : MEDIA_LABELS[kind.value];
});
</script>
