<template>
  <TicketEmails
    :key="ticket"
    :ticket="ticket"
    :extra-activities="extraActivities"
    :version="version"
    :authors="isChat ? authors : null"
    :reserve="reserve"
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
    <template v-if="isChat" #icon-log><span /></template>
    <template v-if="isChat" #item-log="{ activity }">
      <!-- Pulled across the avatar column, so the line centres on the whole thread. -->
      <div
        class="relative z-20 -ms-[38px] flex flex-1 items-center gap-3 py-1 text-p-sm text-ink-gray-5"
      >
        <div class="flex-1 border-t border-outline-gray-2" />
        <span class="shrink-0">
          {{ activity.data.divider }} ·
          <Tooltip
            :text="dayjsLocal(activity.timestamp).format(DATE_FORMATS.tooltip)"
          >
            <span>{{ clockTime(activity.timestamp) }}</span>
          </Tooltip>
        </span>
        <div class="flex-1 border-t border-outline-gray-2" />
      </div>
    </template>
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
          <Tooltip
            :text="dayjsLocal(activity.timestamp).format(DATE_FORMATS.tooltip)"
          >
            <span class="text-ink-gray-5">{{
              clockTime(activity.timestamp)
            }}</span>
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
import { computed, defineComponent, h, ref, watch, type PropType } from "vue";
import { Avatar, Tooltip, dayjs, dayjsLocal } from "frappe-ui";
import {
  ActivityTimeline,
  AttachmentChip,
  useActivityTimeline,
} from "@framework/ui/components/ActivityTimeline";
import { useSession } from "@app/stores/session";
import { conversationLayout } from "@app/stores/settings";
import { DATE_FORMATS } from "@app/utils";
import PortalEmailContent from "./PortalEmailContent.vue";

type Row = {
  type?: string;
  timestamp?: string;
  author?: { email?: string };
  data?: any;
};

// Messages from one side within this window read as one turn.
const GROUP_SECONDS = 5 * 60;

// A component, not the page script: the composable needs a component's setup.
const props = defineProps<{
  ticket: string;
  // The page's own rows, such as closes; merged in by time.
  extraActivities?: Row[];
  // The ticket's `modified`, so a save reloads the emails.
  version?: string;
  // The ticket's communications, which say who wrote each email and whether they are an agent.
  communications?: {
    name: string;
    is_agent: boolean;
    user?: { email?: string };
  }[];
  // The composer's height, kept clear under the last message.
  reserve?: number;
}>();

const isChat = computed(() => conversationLayout.value === "chat");
const session = useSession();

// By email name; the sender address alone can differ for one person, such as admin@ and Administrator.
const authors = computed(
  () =>
    new Map(
      (props.communications || []).map((message) => [
        message.name,
        { isAgent: message.is_agent, email: message.user?.email },
      ])
    )
);

function clockTime(value: string) {
  const at = dayjsLocal(value);
  if (at.isSame(dayjsLocal(), "day")) return at.format(DATE_FORMATS.clock);
  const day = at.isSame(dayjsLocal(), "year") ? "D MMMM" : "D MMMM YYYY";
  return at.format(`${day} [at] ${DATE_FORMATS.clock}`);
}

// Keyed by the ticket above: the composable reads its ticket once, so another ticket remounts it.
const TicketEmails = defineComponent({
  props: {
    ticket: { type: String, required: true },
    extraActivities: { type: Array as PropType<Row[]>, default: () => [] },
    version: String,
    // Set only in the chat layout, where each email gets its side and grouping.
    authors: {
      type: Map as PropType<Map<
        string,
        { isAgent: boolean; email?: string }
      > | null>,
      default: null,
    },
    reserve: { type: Number, default: 0 },
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
      // The page's rows wait for the emails, so a close never shows alone while the thread loads.
      if (loading.value && !activities.value.length) return [];
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
      if (!props.authors) return sorted;
      const placed = sorted.filter(
        (row) => row.type !== "email" || isPlaceable(row)
      );
      return placed.map((row, index) =>
        row.type === "email"
          ? { ...row, chat: chatPlacement(row, placed[index - 1]) }
          : row
      );
    });

    // Guessing an unknown sender's side drew agent replies right, then left; wait for the ticket to say.
    function isPlaceable(row: Row) {
      return (
        props.authors!.has(row.data.name) ||
        row.author?.email === session.config.value?.session_user
      );
    }

    function chatPlacement(row: Row, previous?: Row) {
      const isOwn = !isAgent(row);
      const opensGroup = !(
        previous?.type === "email" &&
        authorEmail(previous) === authorEmail(row) &&
        !isAgent(previous) === isOwn &&
        dayjs(row.timestamp).diff(dayjs(previous.timestamp), "s") <=
          GROUP_SECONDS
      );
      return { isOwn, opensGroup, showAvatar: opensGroup && !isOwn };
    }

    // An email the viewer just sent arrives before the ticket's communications reload
    function isAgent(row: Row) {
      const known = props.authors!.get(row.data.name);
      if (known) return known.isAgent;
      const viewer = session.config.value;
      return (
        row.author?.email === viewer?.session_user && Boolean(viewer?.is_agent)
      );
    }

    function authorEmail(row: Row) {
      return props.authors!.get(row.data.name)?.email || row.author?.email;
    }

    // When the reserve settles after a resize, scroll by the difference so the messages stay put.
    const wrapper = ref<HTMLElement | null>(null);
    watch(
      () => props.reserve,
      (height, previous) => {
        if (!previous) return;
        const scroller =
          wrapper.value?.querySelector<HTMLElement>(".activity-timeline");
        if (scroller) scroller.scrollTop -= height - previous;
      },
      { flush: "post" }
    );

    // ActivityTimeline's root is a fragment, so the page's classes land on this wrapper instead.
    return () =>
      h(
        "div",
        {
          ref: wrapper,
          class: "portal-thread flex flex-col",
          style: { "--composer-reserve": `${props.reserve}px` },
        },
        [
          h(
            ActivityTimeline,
            { activities: rows.value, loading: loading.value, paginate },
            slots
          ),
        ]
      );
  },
});
</script>

<style>
/* Bounded, so the timeline scrolls inside the thread instead of growing past it. */
.portal-thread > .activity-timeline {
  flex: 1 1 0%;
  min-height: 0;
}

/* Spacing inside the scroll, not on the wrapper: messages slide under the header and the composer instead of being cut short. */
.portal-thread > .activity-timeline > div {
  padding-top: 1rem;
  padding-bottom: var(--composer-reserve, 0px);
}

/* Not scoped: ActivityTimeline's root is a fragment, so no class or scope id reaches it. */
.activity-timeline:has(.portal-chat-message)
  .activity
  > div
  > div:first-child::after {
  display: none;
}
</style>
