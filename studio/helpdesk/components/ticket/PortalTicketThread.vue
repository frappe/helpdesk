<template>
  <TicketEmails
    :key="ticket"
    :ticket="ticket"
    :extra-activities="extraActivities"
    :version="version"
    :agent-replies="isChat ? agentReplies : null"
  >
    <template v-for="(_, name) in $slots" #[name]="scope">
      <slot :name="name" v-bind="scope || {}" />
    </template>
    <template v-if="isChat" #icon-email="{ activity }">
      <div class="flex h-10 items-start">
        <Avatar
          v-if="activity.chat.showAvatar"
          size="lg"
          :label="activity.author?.fullname"
          :image="activity.author?.image"
        />
      </div>
    </template>
    <template v-if="isChat" #icon-solve_prompt><span /></template>
    <template v-if="isChat" #item-email="{ activity }">
      <div
        class="portal-chat-message flex w-full flex-col gap-1"
        :class="[
          activity.chat.isOwn ? 'items-end' : 'items-start',
          { '-mt-3': !activity.chat.opensGroup },
        ]"
      >
        <div
          v-if="activity.chat.opensGroup"
          class="flex items-center gap-1 px-1 text-p-sm"
        >
          <span class="font-medium text-ink-gray-8">
            {{ activity.author?.fullname }}
          </span>
          <span class="text-ink-gray-4">·</span>
          <Tooltip :text="dayjs(activity.timestamp).format(DATE_FORMATS.tooltip)">
            <span class="text-ink-gray-5">{{ clockTime(activity.timestamp) }}</span>
          </Tooltip>
        </div>
        <div
          class="w-fit min-w-0 max-w-[76%] rounded-[10px] border px-3 py-1.5"
          :class="
            activity.chat.isOwn
              ? 'border-transparent bg-surface-gray-1'
              : 'border-outline-gray-2 bg-surface-elevation-1'
          "
        >
          <PortalEmailContent :content="activity.data.content" />
          <div
            v-if="activity.data.attachments?.length"
            class="flex flex-wrap gap-2 pb-1 pt-2"
          >
            <AttachmentChip
              v-for="attachment in activity.data.attachments"
              :key="attachment.file_url"
              :label="attachment.file_name"
              :url="attachment.file_url"
            />
          </div>
        </div>
      </div>
    </template>
  </TicketEmails>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, watch, type PropType } from "vue";
import { Avatar, Tooltip, dayjs } from "frappe-ui";
import {
  ActivityTimeline,
  AttachmentChip,
  useActivityTimeline,
} from "@framework/ui/components/ActivityTimeline";
import { conversationLayout } from "@app/stores/settings";
import { DATE_FORMATS } from "@app/utils";
import PortalEmailContent from "./PortalEmailContent.vue";

type Row = { type?: string; timestamp?: string; author?: { email?: string }; data?: any };

// Messages from one side within this window read as one turn.
const GROUP_SECONDS = 5 * 60;

// A component, not the page script: the composable needs a component's setup.
const props = defineProps<{
  ticket: string;
  // The page's own rows, such as closes; merged in by time.
  extraActivities?: Row[];
  // The ticket's `modified`, so a save reloads the emails.
  version?: string;
  // The ticket's communications, which say who sent each email.
  communications?: { name: string; sent_or_received: string }[];
}>();

const isChat = computed(() => conversationLayout.value === "chat");

const agentReplies = computed(
  () =>
    new Set(
      (props.communications || [])
        .filter((message) => message.sent_or_received === "Sent")
        .map((message) => message.name)
    )
);

function clockTime(value: string) {
  const at = dayjs(value);
  if (at.isSame(dayjs(), "day")) return at.format(DATE_FORMATS.clock);
  const day = at.isSame(dayjs(), "year") ? "D MMMM" : "D MMMM YYYY";
  return at.format(`${day} [at] ${DATE_FORMATS.clock}`);
}

// Keyed by the ticket above: the composable reads its ticket once, so another ticket remounts it.
const TicketEmails = defineComponent({
  props: {
    ticket: { type: String, required: true },
    extraActivities: { type: Array as PropType<Row[]>, default: () => [] },
    version: String,
    // Set only in the chat layout, where each email gets its side and grouping.
    agentReplies: { type: Set as PropType<Set<string> | null>, default: null },
  },
  setup(props, { slots }) {
    const { activities, loading, paginate, reload } = useActivityTimeline(
      "HD Ticket",
      props.ticket,
      ["email"]
    );
    watch(
      () => props.version,
      (_, before) => before && reload()
    );
    // A customer never sees who else an email went to.
    const rows = computed(() => {
      const sorted = [
        ...activities.value.map((row) => ({
          ...row,
          data: { ...row.data, to: "", cc: "", bcc: "" },
        })),
        ...props.extraActivities,
      ].sort(
        (first, second) =>
          dayjs(first.timestamp).valueOf() - dayjs(second.timestamp).valueOf()
      );
      if (!props.agentReplies) return sorted;
      // Chat shows only the conversation; closes are timeline rows.
      const chat = sorted.filter((row) => row.type !== "log");
      return chat.map((row, index) =>
        row.type === "email" ? { ...row, chat: chatPlacement(row, chat[index - 1]) } : row
      );
    });

    // A pending reply is not a communication yet, so anything not sent by an agent is the reader's side.
    function chatPlacement(row: Row, previous?: Row) {
      const isOwn = !props.agentReplies!.has(row.data.name);
      const opensGroup = !(
        previous?.type === "email" &&
        previous.author?.email === row.author?.email &&
        !props.agentReplies!.has(previous.data.name) === isOwn &&
        dayjs(row.timestamp).diff(dayjs(previous.timestamp), "s") <= GROUP_SECONDS
      );
      return { isOwn, opensGroup, showAvatar: opensGroup && !isOwn };
    }

    return () =>
      h(
        ActivityTimeline,
        { activities: rows.value, loading: loading.value, paginate },
        slots
      );
  },
});
</script>

<style>
/* Not scoped: ActivityTimeline's root is a fragment, so no class or scope id reaches it. */
.activity-timeline:has(.portal-chat-message) .activity > div > div:first-child::after {
  display: none;
}
</style>
