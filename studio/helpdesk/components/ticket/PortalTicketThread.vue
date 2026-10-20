<template>
  <TicketEmails
    :key="ticket"
    :ticket="ticket"
    :extra-activities="extraActivities"
    :version="version"
    :authors="isChat ? authors : null"
    :reserve="reserve"
  />
</template>

<script setup lang="ts">
import { computed, defineComponent, h, ref, watch, type PropType } from "vue";
import { dayjs } from "frappe-ui";
import {
  ActivityTimeline,
  useActivityTimeline,
} from "@framework/ui/components/ActivityTimeline";
import { plainTextToHtml } from "@helpdesk/shared/utils";
import { useSession } from "@app/stores/session";
import { conversationLayout } from "@app/stores/settings";
import { useChatRows } from "@app/composables/useChatRows";
import PortalChatList from "./PortalChatList.vue";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";

type Row = {
  type?: string;
  timestamp?: string;
  author?: { email?: string };
  data?: any;
};

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

// Keyed by ticket: the composable reads its ticket once.
const TicketEmails = defineComponent({
  props: {
    ticket: { type: String, required: true },
    extraActivities: { type: Array as PropType<Row[]>, default: () => [] },
    version: String,
    // Set in the chat layout, which places each email on a side.
    authors: {
      type: Map as PropType<Map<
        string,
        { isAgent: boolean; email?: string }
      > | null>,
      default: null,
    },
    reserve: { type: Number, default: 0 },
  },
  setup(props) {
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
      return [
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
        ...props.extraActivities.filter(isLoaded),
      ]
        .sort(
          (first, second) =>
            dayjs(first.timestamp).valueOf() - dayjs(second.timestamp).valueOf()
        )
        .filter(
          (row) => !props.authors || row.type !== "email" || isPlaceable(row)
        );
    });
    const chatRows = useChatRows(rows, {
      isCustomer: (row) => !isAgent(row),
      isViewer,
    });

    // Events aren't paged: hold back those older than the oldest loaded email.
    const oldestEmail = computed(() =>
      Math.min(...activities.value.map((row) => dayjs(row.timestamp).valueOf()))
    );
    function isLoaded(row: Row) {
      return (
        !paginate.hasNextPage ||
        dayjs(row.timestamp).valueOf() >= oldestEmail.value
      );
    }

    // Unknown sender: wait for the ticket rather than guess a side.
    function isPlaceable(row: Row) {
      return props.authors!.has(row.data.name) || isViewer(row);
    }

    function isViewer(row: Row) {
      const email =
        props.authors!.get(row.data.name)?.email || row.author?.email;
      return email === session.config.value?.session_user;
    }

    // The viewer's just-sent email precedes the communications reload.
    function isAgent(row: Row) {
      const known = props.authors!.get(row.data.name);
      if (known) return known.isAgent;
      return Boolean(session.config.value?.is_agent);
    }

    // Offset scroll by the reserve change so messages stay put.
    const wrapper = ref<HTMLElement | null>(null);
    watch(
      () => props.reserve,
      (height, previous) => {
        if (!previous) return;
        const scroller = wrapper.value?.firstElementChild;
        // Pinned to the newest (column-reverse: 0), the padding already lifts it.
        if (!scroller || scroller.scrollTop > -2) return;
        scroller.scrollTop -= height - previous;
      },
      { flush: "post" }
    );

    // Sending a message scrolls back to the newest.
    watch(
      () => (props.authors ? chatRows.value.at(-1) : undefined),
      (last, before) => {
        if (!before || last?.key === before.key) return;
        if (last?.kind !== "message" || !last.isViewer) return;
        const scroller = wrapper.value?.firstElementChild;
        if (scroller) scroller.scrollTop = 0;
      },
      { flush: "post" }
    );

    // Fade in only after a first load that showed nothing.
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
            // Chat lines up with the composer; the timeline keeps its gutter.
            props.authors ? "px-3 sm:px-5" : "sm:px-6 lg:px-10",
            revealed.value && "portal-reveal",
          ],
          style: { "--composer-reserve": `${props.reserve}px` },
        },
        [
          isFirstLoad.value
            ? h(PortalSkeleton, {
                variant: "thread",
                // Follows the page skeleton, which already faded in.
                instant: true,
                class: !props.authors && "max-sm:px-4",
              })
            : props.authors
            ? h(PortalChatList, { rows: chatRows.value, paginate })
            : h(ActivityTimeline, {
                activities: rows.value,
                loading: loading.value,
                paginate,
              }),
        ]
      );
  },
});
</script>

<style>
.portal-thread > * {
  flex: 1 1 0%;
  min-height: 0;
}

/* Padding inside the scroller so messages slide under header and composer. */
.portal-thread > * > div {
  padding-top: 1rem;
  padding-bottom: var(--composer-reserve, 0px);
}

/* Email frames copy page sheets; keep their :root transparent. */
:root:has(.email-content) {
  background: transparent;
}
</style>
