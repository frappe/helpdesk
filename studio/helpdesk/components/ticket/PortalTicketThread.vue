<template>
  <TicketEmails
    :key="ticket"
    :ticket="ticket"
    :extra-activities="extraActivities"
    :version="version"
    :authors="isChat ? authors : null"
    :reserve="reserve"
  >
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
      <!-- Pulled over the avatar column to centre on the thread. -->
      <div
        class="relative z-20 -ms-[38px] flex flex-1 items-center gap-3 py-1 text-p-sm text-ink-gray-5"
      >
        <div class="flex-1 border-t border-outline-gray-2" />
        <span class="shrink-0">
          {{ activity.data.divider }} ·
          <Tooltip :text="dateFormat(activity.timestamp)">
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
          <Tooltip :text="dateFormat(activity.timestamp)">
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
import { __ } from "@helpdesk/shared/translation";
import {
  ActivityTimeline,
  AttachmentChip,
  useActivityTimeline,
} from "@framework/ui/components/ActivityTimeline";
import { dateFormat } from "@framework/ui/components/ActivityTimeline/utils";
import { DATE_FORMATS, plainTextToHtml } from "@helpdesk/shared/utils";
import { useSession } from "@app/stores/session";
import { conversationLayout } from "@app/stores/settings";
import PortalEmailContent from "./PortalEmailContent.vue";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";

type Row = {
  type?: string;
  timestamp?: string;
  author?: { email?: string };
  data?: any;
};

const GROUP_SECONDS = 5 * 60;

const props = defineProps<{
  ticket: string;
  extraActivities?: Row[];
  // Changes on save, reloading the emails.
  version?: string;
  communications?: {
    name: string;
    is_agent: boolean;
    user?: { email?: string };
  }[];
  reserve?: number;
}>();

const isChat = computed(() => conversationLayout.value === "chat");
const session = useSession();

// By email name: one person can send from several addresses.
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
  return __("{0} at {1}", [at.format(day), at.format(DATE_FORMATS.clock)]);
}

// Keyed by ticket: the composable reads its ticket once.
const TicketEmails = defineComponent({
  props: {
    ticket: { type: String, required: true },
    extraActivities: { type: Array as PropType<Row[]>, default: () => [] },
    version: String,
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
    // Customers never see other recipients.
    const rows = computed(() => {
      // Wait for emails so a close never shows alone.
      if (loading.value && !activities.value.length) return [];
      const sorted = [
        ...activities.value.map((row) => ({
          ...row,
          data: {
            ...row.data,
            content: plainTextToHtml(row.data.content),
            to: "",
            cc: "",
            bcc: "",
          },
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

    // Unknown sender: wait for the ticket rather than guess a side.
    function isPlaceable(row: Row) {
      return (
        props.authors!.has(row.data.name) ||
        row.author?.email === session.config.value?.session_user
      );
    }

    function chatPlacement(row: Row, previous?: Row) {
      const isOwn = isViewerSide(row);
      const opensGroup = !(
        previous?.type === "email" &&
        authorEmail(previous) === authorEmail(row) &&
        isViewerSide(previous) === isOwn &&
        dayjs(row.timestamp).diff(dayjs(previous.timestamp), "s") <=
          GROUP_SECONDS
      );
      return { isOwn, opensGroup, showAvatar: opensGroup && !isOwn };
    }

    function isViewerSide(row: Row) {
      return isAgent(row) === Boolean(session.config.value?.is_agent);
    }

    // The viewer's just-sent email precedes the communications reload.
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

    // Offset scroll by the reserve change so messages stay put.
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

    // Fade in only when replacing the skeleton.
    const isFirstLoad = computed(
      () => loading.value && !activities.value.length
    );
    const revealed = ref(false);
    watch(isFirstLoad, (first) => !first && (revealed.value = true));

    // ActivityTimeline's root is a fragment; classes go on this wrapper.
    return () =>
      h(
        "div",
        {
          ref: wrapper,
          class: [
            "portal-thread flex flex-col",
            revealed.value && "portal-reveal",
          ],
          style: { "--composer-reserve": `${props.reserve}px` },
        },
        [
          isFirstLoad.value
            ? h(PortalSkeleton, {
                variant: "thread",
                instant: true,
                class: "flex-1 overflow-hidden",
              })
            : h(
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
.portal-thread > .activity-timeline {
  flex: 1 1 0%;
  min-height: 0;
}

/* Padding inside the scroller so messages slide under header and composer. */
.portal-thread > .activity-timeline > div {
  padding-top: 1rem;
  padding-bottom: var(--composer-reserve, 0px);
}

/* Unscoped: no scope id reaches ActivityTimeline's fragment root. */
.activity-timeline:has(.portal-chat-message)
  .activity
  > div
  > div:first-child::after {
  display: none;
}

/* Email frames copy page sheets; keep their :root transparent. */
:root:has(.email-content) {
  background: transparent;
}
</style>
