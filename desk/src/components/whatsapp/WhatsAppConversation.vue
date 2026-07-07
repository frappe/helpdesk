<template>
  <!-- Self-contained WhatsApp channel: a chat thread with its own composer,
       true to the medium — deliberately unlike the email/comment timeline. -->
  <div class="flex h-full flex-col">
    <FadedScrollableDiv
      ref="scrollRef"
      class="flex flex-1 flex-col gap-3 overflow-y-auto px-5 py-4"
      :mask-length="20"
    >
      <template v-if="messages.length">
        <WhatsAppMessageItem
          v-for="message in messages"
          :key="message.key"
          :activity="message"
          @reply="onReply"
          @react="onReact"
          @scroll-to="scrollToMessage"
        />
      </template>
      <div
        v-else
        class="flex flex-1 flex-col items-center justify-center gap-3 text-ink-gray-4"
      >
        <WhatsAppIcon class="size-7" />
        <span class="text-lg font-medium text-ink-gray-8">
          {{ __("No WhatsApp messages") }}
        </span>
        <span class="text-p-sm">{{ __("Start a conversation below.") }}</span>
      </div>
    </FadedScrollableDiv>

    <WhatsAppEditor ref="editorRef" :ticket-id="ticketId" @submit="onSubmit" />
  </div>
</template>

<script setup lang="ts">
import { FadedScrollableDiv } from "@/components";
import { WhatsAppIcon } from "@/components/icons";
import WhatsAppEditor from "@/components/whatsapp/WhatsAppEditor.vue";
import WhatsAppMessageItem from "@/components/whatsapp/WhatsAppMessageItem.vue";
import { __ } from "@/translation";
import { WhatsAppActivity } from "@/types";
import { createResource, toast } from "frappe-ui";
import { PropType, nextTick, ref, watch } from "vue";

const props = defineProps({
  messages: {
    type: Array as PropType<WhatsAppActivity[]>,
    default: () => [],
  },
  ticketId: {
    type: String,
    required: true,
  },
});

const emit = defineEmits<{ update: [] }>();

const scrollRef = ref<InstanceType<typeof FadedScrollableDiv> | null>(null);
const editorRef = ref<InstanceType<typeof WhatsAppEditor> | null>(null);

// One reaction resource for the whole thread, not one per bubble.
const reactResource = createResource({
  url: "helpdesk.integrations.whatsapp.api.react_on_whatsapp_message",
  onSuccess: () => emit("update"),
  onError: (e: Error) => toast.error(e.message || __("Could not react")),
});

function scrollToBottom() {
  nextTick(() => {
    const el = scrollRef.value?.$el as HTMLElement | undefined;
    if (el) el.scrollTop = el.scrollHeight;
  });
}

function scrollToMessage(messageId: string | undefined) {
  if (!messageId) return;
  const el = document.getElementById(messageId) as
    | (HTMLElement & { scrollIntoViewIfNeeded?: () => void })
    | null;
  if (!el) return;
  // scrollIntoViewIfNeeded is non-standard (absent in Firefox) — fall back.
  if (el.scrollIntoViewIfNeeded) el.scrollIntoViewIfNeeded();
  else el.scrollIntoView({ block: "center" });
  el.classList.add("bg-yellow-100");
  setTimeout(() => el.classList.remove("bg-yellow-100"), 1000);
}

function onReply(activity: WhatsAppActivity) {
  editorRef.value?.setReply(activity);
}

function onReact(messageId: string, emoji: string) {
  reactResource.submit({ reply_to: messageId, emoji });
}

function onSubmit() {
  emit("update");
  scrollToBottom();
}

// Keep the newest message in view as the thread grows, and on ticket switch
// (where the count can be identical between two tickets).
watch([() => props.messages.length, () => props.ticketId], scrollToBottom, {
  immediate: true,
});
</script>
