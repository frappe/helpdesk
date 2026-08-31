<template>
  <CommentItem
    :comment="activity"
    :editable="editing"
    @save="saveContent"
    @discard="editing = false"
  >
    <template v-if="!editing" #actions>
      <Dropdown
        placement="right"
        :options="kebabOptions"
        @click="isConfirmingDelete = false"
      >
        <Button
          icon="lucide-more-horizontal"
          class="text-ink-gray-5"
          variant="ghost"
        />
      </Dropdown>
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
import { Button, Dropdown, createResource, toast } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, ref } from "vue";
import TimelineReactions from "./TimelineReactions.vue";

export interface CommentExtras {
  reactions: InstanceType<typeof TimelineReactions>["$props"]["reactions"];
  attachments: Array<{ file_name: string; file_url: string }>;
}

const props = defineProps<{
  activity: CommentActivity;
  extras: CommentExtras;
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

const kebabOptions = computed(() => [
  {
    label: __("Copy link"),
    icon: "lucide-link",
    onClick: () => copyActivityLink("comment", props.activity.data.name),
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
        onConfirmDelete: () => deleteComment.submit(),
        isConfirmingDelete,
      })
    : []),
]);

const saveComment = createResource({ url: "frappe.client.set_value" });
const deleteComment = createResource({
  url: "frappe.client.delete",
  makeParams: () => ({ doctype: "Comment", name: props.activity.data.name }),
  onSuccess() {
    emit("update");
    toast.success(__("Comment deleted successfully."));
  },
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

function toggleReaction(emoji: string) {
  reaction.submit({ comment: props.activity.data.name, emoji });
}
</script>
