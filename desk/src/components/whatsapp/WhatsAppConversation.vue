<template>
  <div
    ref="scroller"
    class="min-h-0 flex-1 overflow-y-auto"
    data-testid="whatsapp-thread"
  >
    <div class="px-3 py-4 sm:px-5">
      <MessageList
        :messages="whatsapp.messages.messages"
        :loading="whatsapp.messages.loading"
        :error="whatsapp.messages.error"
        :sender-name="whatsapp.contactName || __('Contact')"
        :you-label="__('You')"
        :reacted-by-label="__('Reacted by')"
        :reply-label="__('Reply')"
        :replying-to-label="__('Replying to')"
        :react-label="__('React')"
        :failed-message-label="__('Failed to send message')"
        :empty-label="__('No WhatsApp messages yet')"
        :empty-description="__('Messages to and from this contact show up here.')"
        :error-label="__('Could not load the WhatsApp conversation')"
        :today-label="__('Today')"
        :yesterday-label="__('Yesterday')"
        @reply="emit('reply', $event)"
        @react="({ messageName, emoji }) => whatsapp.messages.react(messageName, emoji)"
      />
      <div
        v-if="whatsapp.messages.error && !whatsapp.messages.messages.length"
        class="mt-3 flex justify-center"
      >
        <Button :label="__('Retry')" @click="whatsapp.messages.reload()" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { useResizeObserver } from "@vueuse/core";
import { MessageList, type WhatsAppMessage } from "@whatsapp/ui";
import { Button } from "frappe-ui";
import { nextTick, onMounted, useTemplateRef, watch } from "vue";
import type { TicketWhatsApp } from "./useTicketWhatsApp";

const props = defineProps<{ whatsapp: TicketWhatsApp }>();
const emit = defineEmits<{ reply: [message: WhatsAppMessage] }>();

const scroller = useTemplateRef<HTMLElement>("scroller");
let previousHeight = 0;

// stay on the latest message while the composer slides open and the thread shrinks
useResizeObserver(scroller, keepPinned);

// judged on the pre-resize height, so our own scrolls never unpin; 0 means just shown
function keepPinned() {
  const element = scroller.value;
  if (!element) return;
  const gap = element.scrollHeight - element.scrollTop - previousHeight;
  if (!previousHeight || gap < 8) element.scrollTop = element.scrollHeight;
  previousHeight = element.clientHeight;
}

function scrollToLatest() {
  nextTick(() => {
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight;
  });
}

watch(() => props.whatsapp.messages.messages.length, scrollToLatest);

onMounted(scrollToLatest);
</script>

<style scoped>
/* ponytail: reaches into @whatsapp/ui's bubble markup; drop once the package reveals actions on touch itself */
@media (hover: none) {
  :deep([data-direction] > div > .opacity-0) {
    opacity: 1;
    pointer-events: auto;
  }
}
</style>
