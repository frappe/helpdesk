<template>
  <div
    v-if="pendingActions.length"
    ref="container"
    class="overflow-hidden rounded-lg border border-outline-gray-1 bg-surface-gray-1"
  >
    <div class="flex h-8 items-center gap-1.5 ps-2.5 pe-1.5">
      <LucideInfo class="size-3.5 shrink-0 text-ink-gray-4" />
      <template v-if="sourceLabel">
        <Tooltip :text="sourceLabel">
          <span class="min-w-0 truncate text-sm-medium text-ink-gray-7">
            {{ sourceLabel }}
          </span>
        </Tooltip>
        <span class="shrink-0 text-ink-gray-3">·</span>
      </template>
      <span class="shrink-0 whitespace-nowrap text-sm text-ink-gray-5">
        {{ countSentence }}
      </span>
      <div class="ms-auto flex shrink-0 items-center gap-0.5">
        <Button
          variant="ghost"
          size="xs"
          :aria-expanded="expanded"
          :icon="expanded ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          :label="expanded ? __('Hide actions') : __('Show actions')"
          @click="toggleExpanded"
        />
        <Button
          variant="ghost"
          size="xs"
          icon="lucide-x"
          :label="__('Clear all actions')"
          @click="clear"
        />
      </div>
    </div>
    <div v-if="expanded">
      <div
        v-if="chipActions.length"
        class="flex flex-wrap items-center gap-1.5 px-2.5 pb-2"
      >
        <SavedReplyActionChip
          v-for="action in visibleChips"
          :key="actionKey(action)"
          :action="action"
          @update="updateAction(action, $event)"
          @remove="removeAction(action)"
        />
        <button v-if="overflowCount" type="button" @click="showAllChips = true">
          <Badge theme="gray" variant="outline" size="lg">
            {{ __("+{0} more", overflowCount) }}
          </Badge>
        </button>
      </div>
      <SavedReplyActionComment
        v-if="noteAction"
        :action="noteAction"
        @update:value="setNoteValue"
        @remove="removeAction(noteAction)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { isTagAction } from "@/components/Settings/SavedReplies/components/actionTypes";
import { reloadTicket } from "@/composables/useTicket";
import { userStorage } from "@/composables/userStorage";
import { __ } from "@/translation";
import { RenderedSavedReply, SavedReplyAction } from "@/types";
import { useElementSize } from "@vueuse/core";
import { Badge, Button, Tooltip, createResource, toast } from "frappe-ui";
import { computed, ref } from "vue";
import LucideInfo from "~icons/lucide/info";
import SavedReplyActionChip from "./SavedReplyActionChip.vue";
import SavedReplyActionComment from "./SavedReplyActionComment.vue";

/** Chips beyond this stay hidden until the agent asks for the rest. */
const MAX_VISIBLE_CHIPS = 4;
/** Below this the long sentence squeezes the reply name to nothing. */
const NARROW_WIDTH = 470;

const props = defineProps<{
  ticketId: string;
  doctype: string;
}>();

// Persisted like the draft body, so a refresh keeps text and actions in sync.
// Scoped to the agent: a staged comment must not survive a shift handover.
const pendingActions = userStorage<SavedReplyAction[]>(
  "pendingSavedReplyActions" + props.ticketId,
  []
);
const expanded = userStorage(
  "pendingSavedReplyActionsExpanded" + props.ticketId,
  false
);

const showAllChips = ref(false);
const container = ref<HTMLElement>();
const { width } = useElementSize(container);

const noteAction = computed(() =>
  pendingActions.value.find((action) => action.action_type === "Add Comment")
);

const chipActions = computed(() =>
  pendingActions.value.filter((action) => action.action_type !== "Add Comment")
);

const visibleChips = computed(() =>
  showAllChips.value || chipActions.value.length <= MAX_VISIBLE_CHIPS + 1
    ? chipActions.value
    : chipActions.value.slice(0, MAX_VISIBLE_CHIPS)
);

const overflowCount = computed(
  () => chipActions.value.length - visibleChips.value.length
);

/** Collapsing puts the chip list back to its capped state. */
function toggleExpanded() {
  expanded.value = !expanded.value;
  if (!expanded.value) showAllChips.value = false;
}

// Only one reply is ever staged, so its title is the whole label
const sourceLabel = computed(() => pendingActions.value[0]?.source ?? "");

const countSentence = computed(() => {
  const count = pendingActions.value.length;
  if (width.value && width.value < NARROW_WIDTH) {
    return __("{0} actions after sending", count);
  }
  return count === 1
    ? __("1 action will be applied after sending the email")
    : __("{0} actions will be applied after sending the email", count);
});

/** Stage the actions of an applied saved reply, replacing whatever was staged. */
function add(reply: RenderedSavedReply) {
  pendingActions.value = (reply.actions ?? []).map((action) => ({
    ...action,
    source: reply.title,
    // Kept so the staged comment can report edits and restore
    ...(action.action_type === "Add Comment"
      ? { original_value: action.value }
      : {}),
  }));
}

/** What is staged right now, for the replace confirmation. Null when nothing is. */
function stagedSummary(): { count: number; source: string } | null {
  if (!pendingActions.value.length) return null;
  return { count: pendingActions.value.length, source: sourceLabel.value };
}

// Tags share an action type, so they key on their value too
function actionKey(action: SavedReplyAction): string {
  return isTagAction(action.action_type)
    ? `${action.action_type}:${action.value}`
    : action.action_type;
}

/** Repoint an action, e.g. an escalation routed to a different team. */
function updateAction(action: SavedReplyAction, updated: SavedReplyAction) {
  const index = pendingActions.value.indexOf(action);
  if (index !== -1) pendingActions.value[index] = updated;
}

function removeAction(action: SavedReplyAction) {
  pendingActions.value = pendingActions.value.filter(
    (pending) => actionKey(pending) !== actionKey(action)
  );
}

// Whatever is in the editor at send time is what gets applied
function setNoteValue(value: string) {
  if (noteAction.value) noteAction.value.value = value;
}

const applyActions = createResource({
  url: "helpdesk.api.saved_replies.apply_saved_reply_actions",
  onSuccess: (result: {
    applied: SavedReplyAction[];
    skipped: SavedReplyAction[];
  }) => {
    if (result.applied?.length) {
      toast.success(
        __("Applied {0} saved reply action(s)", result.applied.length)
      );
    }
    if (result.skipped?.length) {
      toast.warning(
        __(
          "Skipped {0} saved reply action(s) that are no longer valid",
          result.skipped.length
        )
      );
    }
    pendingActions.value = [];
    reloadTicket(props.ticketId);
  },
  onError: (error: { messages?: string[]; status?: number }) => {
    // An error response means the request rolled back, so nothing was applied
    // and the batch is safe to keep staged. Without a status we never heard
    // back and it may have landed — drop it rather than risk applying twice.
    const rolledBack = Boolean(error?.status);
    if (!rolledBack) pendingActions.value = [];
    toast.error(
      error?.messages?.[0] ||
        (rolledBack
          ? __("Could not apply saved reply actions")
          : __("Could not apply saved reply actions, apply them manually"))
    );
    reloadTicket(props.ticketId);
  },
});

/** Apply the staged actions to the ticket; call after the email is sent. */
function submit() {
  if (!pendingActions.value.length || props.doctype !== "HD Ticket") return;
  // Actions stay staged during the request, so guard the second call
  if (applyActions.loading) return;
  applyActions.submit({
    ticket_id: props.ticketId,
    actions: [...pendingActions.value],
  });
}

/** Drop the staged actions without applying them. */
function clear() {
  pendingActions.value = [];
}

defineExpose({ add, stagedSummary, submit, clear });
</script>
