<template>
  <ActivityHeader :title="tabLabel" />
  <TimelineContainer>
    <ActivityTimeline
      ref="timelineRef"
      class="px-5 pt-1 pb-6"
      :activities="filtered"
      :loading="_loading"
      :paginate="paginate"
    >
      <template #empty>
        <div
          class="flex h-full flex-col items-center justify-center gap-2 text-ink-gray-4"
        >
          <component :is="emptyIcon" class="size-6" />
          <p class="text-p-base text-ink-gray-5">
            {{ __("No {0} yet", [tabLabel]) }}
          </p>
        </div>
      </template>

      <!-- reuse the framework row, bolding tag names alongside the actor -->
      <template #item-log="{ activity }">
        <LogItem :activity="withTagNamesBold(activity)" />
      </template>

      <template #item-comment="{ activity }">
        <TimelineCommentRow
          :activity="activity"
          :extras="extrasFor(activity.data.name)"
          @update="refresh"
        />
      </template>

      <template #item-email="{ activity }">
        <EmailItem :email="withEmailFixups(activity)">
          <template #actions>
            <Button
              variant="ghost"
              :tooltip="__('Reply')"
              @click="reply(activity)"
            >
              <template #icon><ReplyIcon class="text-ink-gray-7" /></template>
            </Button>
            <Button
              variant="ghost"
              :tooltip="__('Reply All')"
              @click="replyAll(activity)"
            >
              <template #icon
                ><ReplyAllIcon class="text-ink-gray-7"
              /></template>
            </Button>
            <Dropdown placement="right" :options="emailOptions(activity)">
              <Button
                icon="lucide-more-horizontal"
                class="!text-ink-gray-7"
                variant="ghost"
              />
            </Dropdown>
          </template>
        </EmailItem>
      </template>

      <template #item-call="{ activity }">
        <CallArea :activity="activity.data" />
      </template>
      <template #icon-call="{ activity }">
        <FeatherIcon
          :name="
            activity.data.call_type === 'Incoming'
              ? 'phone-incoming'
              : 'phone-outgoing'
          "
          class="size-4 text-ink-gray-5"
        />
      </template>
    </ActivityTimeline>
  </TimelineContainer>
  <TicketSplitModal
    :modelValue="Boolean(splitCommunication)"
    @update:modelValue="splitCommunication = ''"
    :ticket_id="ticketId"
    :communication_id="splitCommunication"
  />
</template>

<script lang="ts">
import type { VisibleTypes } from "@framework/ui";

// the only field changes worth a feed row; everything else is noise the old
// feed never showed
const VERSION_FIELDS = [
  "status",
  "priority",
  "agent_group",
  "ticket_type",
  "sla",
  "custom_members",
];

// one key for every tab: the composable caches resources per visibleTypes, so
// all tab instances share a single fetch; tabs filter client-side
export const SHARED_VISIBLE_TYPES: VisibleTypes = [
  "email",
  "comment",
  "log",
  "attachment_log",
  { version: VERSION_FIELDS },
];
</script>

<script setup lang="ts">
import CallArea from "@/components/CallArea.vue";
import {
  ActivityIcon,
  CommentIcon,
  EmailIcon,
  PhoneIcon,
  ReplyAllIcon,
  ReplyIcon,
} from "@/components/icons";
import ActivityHeader from "@/components/ticket/ActivityHeader.vue";
import TicketSplitModal from "@/components/ticket/TicketSplitModal.vue";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { copyActivityLink } from "@/utils";
import {
  ActivityTimeline,
  EmailItem,
  LogItem,
  TimelineContainer,
  useActivityTimeline,
  type Activity,
  type CustomActivity,
  type EmailActivity,
  type LogActivity,
} from "@framework/ui";
import { Button, Dropdown, FeatherIcon, createResource } from "frappe-ui";
import {
  computed,
  inject,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  useTemplateRef,
  watch,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideSplit from "~icons/lucide/split";
import TimelineCommentRow, { CommentExtras } from "./TimelineCommentRow.vue";

const props = defineProps<{
  ticketId: string;
  tab: string;
  tabLabel: string;
}>();
const emit = defineEmits<{ "email:reply": [payload: object] }>();

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const { getUser } = useUserStore();
const { $socket } = globalStore();
const ticket = inject(TicketSymbol)!;

const splitCommunication = ref("");
const timelineRef =
  useTemplateRef<InstanceType<typeof ActivityTimeline>>("timelineRef");

const { activities, loading, paginate, reload } = useActivityTimeline(
  "HD Ticket",
  props.ticketId,
  SHARED_VISIBLE_TYPES
);

const calls = createResource({
  url: "helpdesk.api.timeline.get_ticket_calls",
  makeParams: () => ({ ticket: props.ticketId }),
  cache: ["ticket-calls", props.ticketId],
  auto: props.tab === "activity" || props.tab === "call",
});

const _loading = computed(() => loading.value || calls.loading);

const extras = createResource({
  url: "helpdesk.api.timeline.get_comment_extras",
  makeParams: () => ({ ticket: props.ticketId }),
  cache: ["comment-extras", props.ticketId],
  auto: props.tab === "activity" || props.tab === "comment",
});

const feed = computed<Array<Activity | CustomActivity>>(() => {
  const callRows: CustomActivity[] = (calls.data ?? []).map((call: any) => ({
    type: "call",
    key: `call:${call.name}`,
    timestamp: call.creation,
    data: { ...call, call_type: call.type },
  }));
  return [...activities.value, ...callRows].sort((a, b) =>
    (a.timestamp ?? "").localeCompare(b.timestamp ?? "")
  );
});

// version fieldnames and noisy types are trimmed server-side (shared fetch);
// per-tab type selection and the created/edited log cut happen here
const filtered = computed(() => {
  const rows = feed.value.filter(
    (a) =>
      !(a.type === "log" && ["edited", "created"].includes(a.data?.subtype))
  );
  if (props.tab === "activity") return rows;
  return rows.filter((a) => a.type === props.tab);
});

const emptyIcon = computed(
  () =>
    ({
      email: EmailIcon,
      comment: CommentIcon,
      call: PhoneIcon,
    }[props.tab] ?? ActivityIcon)
);

function emailOptions(activity: EmailActivity) {
  return [
    {
      label: __("Copy link"),
      icon: "lucide-link",
      onClick: () => copyActivityLink("communication", activity.data.name),
    },
    ...(showSplitOption(activity)
      ? [
          {
            label: __("Split Ticket"),
            icon: LucideSplit,
            onClick: () => (splitCommunication.value = activity.data.name),
          },
        ]
      : []),
  ];
}

function extrasFor(comment: string): CommentExtras {
  return extras.data?.[comment] ?? { reactions: [], attachments: [] };
}

function refresh() {
  reload();
  extras.reload();
}

// after send/comment the newest row belongs on screen (old feed parity)
async function refreshAndScroll() {
  await Promise.allSettled([reload(), extras.reload()]);
  nextTick(() => timelineRef.value?.scrollToLatest());
}

// "added tags a, b & removed tag c" -> names into assignees, which splitBold
// renders dark like the actor
function withTagNamesBold(activity: LogActivity): LogActivity {
  if (activity.data?.subtype !== "info") return activity;
  const text = activity.data.text ?? "";
  const names = [...text.matchAll(/(?:added|removed) tags? ([^&]+)/g)]
    .flatMap((m) => m[1].split(","))
    .map((s) => s.trim())
    .filter(Boolean);
  if (!names.length) return activity;
  return {
    ...activity,
    data: {
      ...activity.data,
      assignees: [...(activity.data.assignees ?? []), ...names],
    },
  };
}

function withEmailFixups(activity: EmailActivity): EmailActivity {
  const data = { ...activity.data };
  // portal tickets have no real delivery pipeline; hide the badge
  if (ticket.value?.doc?.via_customer_portal) delete data.deliveryStatus;
  if (isPlainText(data.content)) {
    data.content = data.content.replace(/\n/g, "<br>");
  }
  return { ...activity, data };
}

function isPlainText(content: string): boolean {
  return !/<[a-z][\s\S]*>/i.test(content ?? "");
}

function isFirstEmail(activity: EmailActivity): boolean {
  const emails = feed.value.filter((a) => a.type === "email");
  return emails[0]?.key === activity.key;
}

function showSplitOption(activity: EmailActivity): boolean {
  return !isFirstEmail(activity) && ticket.value?.doc?.status !== "Closed";
}

// sender is an email address; userId may be the raw session user
function isSelf(email: string): boolean {
  return (
    authStore.userId === email || getUser(authStore.userId)?.email === email
  );
}

function reply(activity: EmailActivity) {
  const { sender, content } = activity.data;
  emit("email:reply", {
    content,
    to: isSelf(sender) ? activity.data.to : sender,
  });
}

function replyAll(activity: EmailActivity) {
  const { sender, to, cc, bcc, content } = activity.data;
  const exclude = [authStore.userId, getUser(authStore.userId)?.email, sender];
  const filteredTo = splitRecipients(to, exclude);
  const filteredCc = splitRecipients(cc, exclude);
  const filteredBcc = splitRecipients(bcc, exclude);
  const isSender = isSelf(sender);
  emit("email:reply", {
    content,
    to: isSender ? filteredTo.join(", ") : sender,
    cc: isSender ? filteredCc : [...filteredTo, ...filteredCc],
    bcc: filteredBcc,
  });
}

// comma split that respects quoted display names: '"Kapoor, Riya" <r@x>'
function splitRecipients(
  field: string | undefined,
  exclude: string[]
): string[] {
  const parts: string[] = [];
  let current = "";
  let inQuotes = false;
  for (const char of field ?? "") {
    if (char === '"') {
      inQuotes = !inQuotes;
      current += char;
    } else if (char === "," && !inQuotes) {
      parts.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  if (current) parts.push(current.trim());
  return parts.filter(Boolean).filter((item) => !exclude.includes(item));
}

// deep links arrive as ?highlight=comment-<name> / communication-<name>;
// framework row ids are comment:<name> / email:<name>
function scrollToHighlight() {
  const raw = route.query.highlight;
  if (typeof raw !== "string") return;
  const rowId = raw
    .replace(/^comment-/, "comment:")
    .replace(/^communication-/, "email:");
  nextTick(() => {
    // false means the row is not rendered yet; keep ?highlight for the next tick
    if (!timelineRef.value?.scrollToRow(rowId)) return;
    const query = { ...route.query };
    delete query.highlight;
    router.replace({ query, hash: route.hash });
  });
}

// opening at the newest row is the timeline's own job (useTimelineScroll)
watch(
  () => [route.query.highlight, _loading.value, filtered.value.length],
  () => {
    if (_loading.value || !route.query.highlight) return;
    scrollToHighlight();
  }
);

onMounted(() => {
  $socket.on(
    "helpdesk:comment-reaction-update",
    (data: { ticket_id: string }) => {
      if (data.ticket_id === props.ticketId) extras.reload();
    }
  );
});

onBeforeUnmount(() => {
  $socket.off("helpdesk:comment-reaction-update");
});

defineExpose({ reload: refreshAndScroll });
</script>
