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
        :can-reply="whatsapp.canReply"
        :sender-name="whatsapp.contactName || __('Contact')"
        :you-label="__('You')"
        :reacted-by-label="__('Reacted by')"
        :reply-label="__('Reply')"
        :replying-to-label="__('Replying to')"
        :react-label="__('React')"
        :failed-message-label="__('Failed to send message')"
        :empty-label="__('No WhatsApp messages yet')"
        :empty-description="
          __('Messages to and from this contact show up here.')
        "
        :error-label="__('Could not load the WhatsApp conversation')"
        :today-label="__('Today')"
        :yesterday-label="__('Yesterday')"
        @reply="emit('reply', $event)"
        @react="
          ({ messageName, emoji }) =>
            whatsapp.messages.react(messageName, emoji)
        "
      >
        <template #actions="{ message }">
          <Button
            v-if="mentionedTicket(message)"
            variant="ghost"
            size="xs"
            :tooltip="__('Open ticket #{0}', [mentionedTicket(message)])"
            :aria-label="__('Open ticket #{0}', [mentionedTicket(message)])"
            :route="{
              name: 'TicketAgent',
              params: { ticketId: mentionedTicket(message) },
            }"
          >
            <template #icon>
              <LucideArrowUpRight class="size-4 text-ink-gray-7" />
            </template>
          </Button>
        </template>
      </MessageList>
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
import LucideArrowUpRight from "~icons/lucide/arrow-up-right";
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

// our own messages naming another ticket, like the new-ticket notice on a closed one
function mentionedTicket(message: WhatsAppMessage): string | undefined {
  if (message.direction !== "Outgoing") return;
  const ticket = message.message?.match(/#(\d+)/)?.[1];
  return ticket && ticket !== props.whatsapp.ticketName ? ticket : undefined;
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
/* reaches into @whatsapp/ui's bubble markup; drop once the package reveals actions on touch itself */
@media (hover: none) {
  :deep([data-direction] > div > .opacity-0) {
    opacity: 1;
    pointer-events: auto;
  }
}
</style>
