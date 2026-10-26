<template>
  <div
    class="portal-thread is-chat flex flex-col [&>*>div]:px-3 sm:[&>*>div]:px-5"
  >
    <PortalSkeleton
      v-if="!messages.data && !messages.error"
      variant="thread"
      layout="chat"
      instant
    />
    <div
      v-else-if="!messages.data"
      class="flex flex-1 flex-col items-center justify-center gap-3 py-16 text-center"
      data-testid="whatsapp-error"
    >
      <p class="text-p-base text-ink-gray-6">
        {{ __("Could not load this conversation.") }}
      </p>
      <Button variant="subtle" :label="__('Retry')" @click="messages.fetch()" />
    </div>
    <template v-else>
      <p
        v-if="!installed"
        class="px-3 py-4 text-center text-p-base text-ink-gray-5"
        data-testid="whatsapp-unavailable"
      >
        {{ __("This conversation is not available right now.") }}
      </p>
      <PortalChatList v-else :rows="rows" />
      <p
        v-if="installed && !locked"
        class="!flex-none border-t border-outline-gray-1 px-4 py-3 text-center text-p-sm text-ink-gray-6"
      >
        <a
          v-if="businessNumber"
          :href="`https://wa.me/${businessNumber}`"
          target="_blank"
          rel="noopener"
          class="text-ink-gray-8 underline underline-offset-2 hover:text-ink-gray-9"
        >
          {{ __("Reply to this ticket on WhatsApp.") }}
        </a>
        <template v-else>
          {{ __("Reply to this ticket on WhatsApp.") }}
        </template>
      </p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { Button, createResource, dayjs } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { useSession } from "@app/stores/session";
import { useChatRows } from "@app/composables/useChatRows";
import PortalChatList from "@app/components/ticket/PortalChatList.vue";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";

type Activity = {
  type?: string;
  key?: string;
  timestamp: string;
  data?: any;
  author?: any;
};

const props = defineProps<{
  ticket: string;
  // The customer's name on their messages.
  contactName?: string;
  // The contact's email: their own bubbles read as the viewer's.
  raisedBy?: string;
  extraActivities?: Activity[];
  // Changes on save, reloading the messages.
  version?: string;
  // A closed ticket takes no replies: the next message raises the prompt.
  locked?: boolean;
}>();

const session = useSession();

const messages = createResource({
  url: "helpdesk.integrations.whatsapp.api.get_messages",
  makeParams: () => ({ ticket: props.ticket }),
});

// Without the whatsapp app nothing reaches the ticket, so no reply hint.
const installed = computed(() => messages.data?.installed !== false);

// Digits only, for a wa.me link; null when Meta couldn't tell us.
const businessNumber = computed(() => messages.data?.business_number);

const activities = computed<Activity[]>(() =>
  [
    ...(messages.data?.messages || []).map(toActivity),
    ...(props.extraActivities || []),
  ].sort(
    (first, second) =>
      dayjs(first.timestamp).valueOf() - dayjs(second.timestamp).valueOf()
  )
);

const rows = useChatRows(activities, {
  isCustomer: (activity) => activity.data.direction === "Incoming",
  isViewer: (activity) =>
    activity.data.direction === "Incoming" &&
    props.raisedBy === session.config.value?.session_user,
});

// Outgoing messages come from the business, not a named agent.
function toActivity(message): Activity {
  const isIncoming = message.direction === "Incoming";
  return {
    type: "whatsapp",
    key: `whatsapp:${message.name}`,
    timestamp: message.creation,
    author: isIncoming
      ? { fullname: props.contactName }
      : { fullname: session.brandName.value, image: session.brandLogo.value },
    data: message,
  };
}

// Pings mid-fetch end in one trailing fetch, so a stale reply never lands last.
let refetchQueued = false;
function refresh() {
  if (!props.ticket) return;
  if (messages.loading) refetchQueued = true;
  else messages.fetch();
}

watch(() => [props.ticket, props.version], refresh, { immediate: true });
watch(
  () => messages.loading,
  (loading) => {
    if (loading || !refetchQueued) return;
    refetchQueued = false;
    messages.fetch();
  }
);
</script>
