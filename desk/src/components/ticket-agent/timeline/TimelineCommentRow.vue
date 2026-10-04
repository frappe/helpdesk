<template>
  <CommentItem
    :comment="activity"
    :editable="editing"
    @save="saveContent"
    @discard="editing = false"
  >
    <!-- the framework header has no spot beside the name, so the row draws its own -->
    <template #header>
      <div class="flex h-10 items-center justify-between gap-2">
        <div class="flex min-w-0 items-center gap-2 leading-6">
          <span class="truncate text-base font-medium text-ink-gray-6">
            {{ activity.author.fullname }}
          </span>
          <Badge v-if="pinned" theme="gray" :label="__('Pinned')">
            <template #prefix><PinIcon class="size-3" /></template>
          </Badge>
        </div>
        <div class="flex items-center gap-2">
          <Tooltip :text="postedAt.format(TOOLTIP_DATE_FORMAT)">
            <span class="whitespace-nowrap text-sm leading-6 text-ink-gray-5">
              {{ postedAt.fromNow() }}
            </span>
          </Tooltip>
          <!-- -me-1.5 matches the tighter edge the framework gives a header with actions -->
          <div v-if="!editing" class="-me-1.5">
            <Dropdown
              align="end"
              :options="kebabOptions"
              @update:open="(open) => open && (isConfirmingDelete = false)"
            >
              <Button
                icon="lucide-more-horizontal"
                class="text-ink-gray-5"
                variant="ghost"
              />
            </Dropdown>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <div v-if="extras.attachments.length" class="flex flex-wrap gap-2 mt-2">
        <AttachmentChip
          v-for="file in extras.attachments"
          :key="file.file_url"
          :label="file.file_name"
          :url="file.file_url"
        />
      </div>
      <TimelineReactions
        v-if="reactionsEnabled"
        :reactions="extras.reactions"
        @toggle="toggleReaction"
      />
    </template>
  </CommentItem>
</template>

<script setup lang="ts">
import { PinIcon, UnpinIcon } from "@/components/icons";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";
import { ConfirmDelete, copyActivityLink, isContentEmpty } from "@/utils";
import {
  AttachmentChip,
  CommentItem,
  type CommentActivity,
} from "@framework/ui/ActivityTimeline";
import {
  Badge,
  Button,
  Dropdown,
  Tooltip,
  createResource,
  dayjsLocal,
  toast,
} from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, h, ref } from "vue";
import TimelineReactions from "./TimelineReactions.vue";

export interface CommentExtras {
  reactions: InstanceType<typeof TimelineReactions>["$props"]["reactions"];
  attachments: Array<{ file_name: string; file_url: string }>;
}

// mirrors MAX_PINNED_COMMENTS in helpdesk/extends/comment.py, which enforces it
const MAX_PINNED_COMMENTS = 5;
// same as the framework's timeline, so every row's time reads alike
const TOOLTIP_DATE_FORMAT = "ddd, MMM D, YYYY h:mm A";

const props = defineProps<{
  activity: CommentActivity;
  extras: CommentExtras;
  pinned: boolean;
  pinCount: number;
}>();
const emit = defineEmits<{ update: [] }>();

const authStore = useAuthStore();
const { getUser } = useUserStore();
const { enableCommentReactions: reactionsEnabled } = storeToRefs(
  useConfigStore()
);

const editing = ref(false);
const isConfirmingDelete = ref(false);

// author.email is the resolved address; userId may be the raw session user
// ("Administrator"), so match either form
const isOwner = computed(() => {
  const authorEmail = props.activity.author?.email;
  return (
    authStore.userId === authorEmail ||
    getUser(authStore.userId)?.email === authorEmail
  );
});
const isMergeMarker = computed(() =>
  /has been merged with ticket #\d+/.test(props.activity.data.content)
);
const postedAt = computed(() => dayjsLocal(props.activity.timestamp));
const pinLimitReached = computed(
  () => !props.pinned && props.pinCount >= MAX_PINNED_COMMENTS
);

const kebabOptions = computed(() => [
  {
    label: __("Copy link"),
    icon: "lucide-link",
    onClick: () => copyActivityLink("comment", props.activity.data.name),
  },
  {
    label: props.pinned ? __("Unpin") : __("Pin"),
    icon: h(props.pinned ? UnpinIcon : PinIcon, { class: "size-4" }),
    onClick: togglePin,
    ...(pinLimitReached.value && {
      disabled: true,
      slots: { label: pinLimitLabel },
    }),
  },
  // only the author edits or deletes; anyone may share the link
  ...(isOwner.value && !isMergeMarker.value
    ? [
        {
          label: __("Edit"),
          icon: "lucide-edit-2",
          onClick: () => (editing.value = true),
        },
      ]
    : []),
  ...(isOwner.value
    ? ConfirmDelete({
        onConfirmDelete: () =>
          toast.promise(deleteComment.submit(), {
            loading: __("Deleting comment"),
            success: __("Comment deleted"),
            error: __("Could not delete the comment"),
          }),
        isConfirmingDelete,
      })
    : []),
]);

const saveComment = createResource({ url: "frappe.client.set_value" });
const deleteComment = createResource({
  url: "frappe.client.delete",
  makeParams: () => ({ doctype: "Comment", name: props.activity.data.name }),
  onSuccess: () => emit("update"),
  // the toast below reports the failure; this keeps the global handler off it
  onError: () => {},
});
const reaction = createResource({
  url: "helpdesk.api.comment.toggle_reaction",
  onSuccess: () => emit("update"),
});

function saveContent(content: string) {
  if (isContentEmpty(content)) {
    toast.error(__("Comment cannot be empty."));
    return;
  }
  saveComment.submit(
    {
      doctype: "Comment",
      name: props.activity.data.name,
      fieldname: "content",
      value: content,
    },
    {
      onSuccess: () => {
        editing.value = false;
        emit("update");
        toast.success(__("Comment updated successfully."));
      },
    }
  );
}

// disabled menu items drop pointer events, so the label opts back in for the tooltip
function pinLimitLabel() {
  const reason = __("{0} pinned already. Unpin one to pin this.", [
    MAX_PINNED_COMMENTS,
  ]);
  return h(Tooltip, { text: reason, side: "right" }, () =>
    h("div", { class: "pointer-events-auto truncate" }, __("Pin"))
  );
}

// any agent may pin; the server caps pins per ticket and says so on failure
function togglePin() {
  saveComment.submit(
    {
      doctype: "Comment",
      name: props.activity.data.name,
      fieldname: "is_pinned",
      value: props.pinned ? 0 : 1,
    },
    {
      onSuccess: () => emit("update"),
      onError: (error: { messages?: string[] }) =>
        toast.error(error.messages?.[0] ?? __("Could not pin the comment")),
    }
  );
}

function toggleReaction(emoji: string) {
  reaction.submit({ comment: props.activity.data.name, emoji });
}
</script>
