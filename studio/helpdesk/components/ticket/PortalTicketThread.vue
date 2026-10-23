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
import {
  computed,
  defineComponent,
  h,
  nextTick,
  ref,
  watch,
  type PropType,
} from "vue";
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
    // Email frames open at a fixed height and fit once loaded and styled, so
    // the skeleton stays over them until then; tall emails would flash squashed.
    const settled = ref(!isFirstLoad.value);
    watch(isFirstLoad, async (first) => {
      if (first) return;
      await nextTick();
      if (wrapper.value) await framesFitted(wrapper.value);
      settled.value = revealed.value = true;
    });

    // ActivityTimeline's root is a fragment; classes go on this wrapper.
    return () =>
      h(
        "div",
        {
          ref: wrapper,
          class: [
            "portal-thread flex flex-col",
            // Both keep their gutter inside the scroller, so the scrollbar sits
            // at the container edge; chat's lines up with the composer.
            props.authors
              ? "is-chat [&>*>div]:px-3 sm:[&>*>div]:px-5"
              : "[&_.activities]:mt-0 sm:[&>.activity-timeline]:px-6 lg:[&>.activity-timeline]:px-10",
            revealed.value && "portal-reveal",
            !settled.value && "is-settling relative",
          ],
          style: { "--composer-reserve": `${props.reserve}px` },
        },
        [
          !settled.value &&
            h(PortalSkeleton, {
              variant: "thread",
              // Follows the page skeleton, which already faded in.
              instant: true,
              class: "absolute inset-0",
            }),
          isFirstLoad.value
            ? null
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

// Each frame fits on load and again as its copied stylesheets load. Capped, so
// one stuck frame cannot hide the thread.
function framesFitted(root: HTMLElement) {
  const frames = [...root.querySelectorAll("iframe")].map(frameStyled);
  const cap = new Promise((resolve) => setTimeout(resolve, 1000));
  return Promise.race([Promise.all(frames), cap]).then(
    () => new Promise((resolve) => requestAnimationFrame(resolve))
  );
}

function frameStyled(frame: HTMLIFrameElement) {
  return new Promise((resolve) =>
    frame.addEventListener(
      "load",
      () => {
        const sheets = [
          ...(frame.contentDocument?.querySelectorAll<HTMLLinkElement>(
            'link[rel="stylesheet"]'
          ) || []),
        ].filter((link) => !link.sheet);
        Promise.all(
          sheets.map(
            (link) =>
              new Promise((done) => {
                link.addEventListener("load", done);
                link.addEventListener("error", done);
              })
          )
        ).then(resolve);
      },
      { once: true }
    )
  );
}
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

/* Laid out, so the frames load and measure, but not shown yet. */
.portal-thread.is-settling > :not(.portal-skeleton) {
  visibility: hidden;
}

/* Email frames copy page sheets; keep their :root transparent. */
:root:has(.email-content) {
  background: transparent;
}

/* frappe-ui's email frame wraps content in the desk's .prose-f; same rules as desk/src/index.css. */
.prose-f {
  @apply break-normal max-w-none prose prose-code:break-all prose-code:whitespace-pre-wrap prose-img:border prose-img:rounded-6 prose-sm;
}
.prose-f * {
  unicode-bidi: plaintext;
}
.prose-f:not(.not-prose):not(.not-prose *) pre {
  background-color: var(--surface-gray-2);
  color: var(--ink-gray-9);
}
</style>
