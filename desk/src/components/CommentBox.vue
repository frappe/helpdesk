<template>
  <div class="flex-col text-base flex-1" ref="commentBoxRef">
    <div class="mb-2 flex items-center justify-between">
      <div class="text-gray-600 flex items-center gap-2">
        <Avatar
          size="md"
          :label="commenter"
          :image="getUser(commentedBy).user_image"
        />
        <p>
          <span class="font-medium text-gray-800">
            {{ commenter }}
          </span>
          <span> {{ __(" commented") }}</span>
        </p>
      </div>
      <div class="flex items-center gap-1">
        <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
          <span class="pl-0.5 text-sm text-gray-600">
            {{ timeAgo(creation) }}
          </span>
        </Tooltip>
        <div v-if="authStore.userId === commentedBy && !editable">
          <Dropdown
            :placement="'right'"
            :options="dropdownOptions"
            @click="isConfirmingDelete = false"
          >
            <Button
              icon="more-horizontal"
              class="text-gray-600"
              variant="ghost"
            />
          </Dropdown>
        </div>
      </div>
    </div>
    <div
      :id="`comment-${name}`"
      class="rounded-md bg-surface-gray-1 transition-colors px-3 py-1.5"
    >
      <TextEditor
        :editor-class="[
          'prose-f shrink text-p-sm transition-all duration-300 ease-in-out block w-full content',
          getFontFamily(_content),
        ]"
        :content="_content"
        :editable="editable"
        :bubble-menu="textEditorMenuButtons"
        :mentions="userMentions"
        @change="(event:string) => {_content = event}"
        @keydown.ctrl.enter.capture.stop="handleSaveComment"
        @keydown.meta.enter.capture.stop="handleSaveComment"
      >
        <template #bottom v-if="editable">
          <div class="flex flex-row-reverse gap-2">
            <div>
              <Button
                :label="
                  isMobileView
                    ? 'Save'
                    : isMac
                    ? 'Save (⌘ + ⏎)'
                    : 'Save (Ctrl + ⏎)'
                "
                @click="handleSaveComment"
                variant="solid"
              />
            </div>
            <Button label="Discard" @click="handleDiscard" />
          </div>
        </template>
      </TextEditor>
      <div
        class="flex flex-wrap gap-2 mb-2"
        v-if="!editable && Boolean(attachments.length)"
      >
        <AttachmentItem
          v-for="a in attachments"
          :key="a.file_url"
          :label="a.file_name"
          :url="a.file_url"
        />
      </div>
      <div
        class="flex items-center gap-2 my-2"
        v-if="!editable && enableCommentReactions"
      >
        <Popover>
          <template #target="{ togglePopover }">
            <button
              class="flex h-full items-center justify-center rounded-full bg-surface-gray-2 px-1 py-1 text-ink-gray-6 transition hover:bg-surface-gray-3"
              @click="togglePopover()"
            >
              <ReactionIcon class="w-4 h-4" />
            </button>
          </template>
          <template #body>
            <div
              class="bg-surface-white rounded-lg shadow-lg p-2 border border-outline-gray-2"
            >
              <div class="grid grid-cols-6 gap-2">
                <button
                  v-for="emoji in emojiList"
                  :key="emoji"
                  class="size-6 flex items-center justify-center rounded hover:bg-surface-gray-2 text-lg transition-colors"
                  @click="handleReaction(emoji)"
                >
                  {{ emoji }}
                </button>
              </div>
            </div>
          </template>
        </Popover>

        <template v-for="reaction in reactionsList" :key="reaction.emoji">
          <Tooltip>
            <template #body>
              <div
                class="bg-surface-gray-7 px-2 py-1 text-center text-p-xs text-ink-white shadow-xl rounded"
              >
                <span v-for="(user, idx) in reaction.users" :key="user.user"
                  >{{ user.full_name
                  }}<span v-if="idx < reaction.users.length - 1">, </span></span
                >
              </div>
            </template>
            <button
              class="flex items-center gap-1 px-2 py-1 rounded-full text-sm transition-colors"
              :class="
                reaction.current_user_reacted
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'bg-surface-gray-3 text-ink-gray-6 hover:bg-surface-gray-4'
              "
              v-if="reaction.count !== 0"
              @click="handleReaction(reaction.emoji)"
            >
              <span>{{ reaction.emoji }}</span>
              <span class="font-medium">{{ reaction.count }}</span>
            </button>
          </Tooltip>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AttachmentItem } from "@/components";
import ReactionIcon from "@/components/icons/ReactionIcon.vue";
import { useDevice } from "@/composables";
import { useScreenSize } from "@/composables/screen";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { updateRes as updateComment } from "@/stores/knowledgeBase";
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";
import { CommentActivity } from "@/types";
import {
  ConfirmDelete,
  dateFormat,
  dateTooltipFormat,
  getFontFamily,
  isContentEmpty,
  textEditorMenuButtons,
  timeAgo,
} from "@/utils";
import {
  Avatar,
  Dropdown,
  Popover,
  TextEditor,
  Tooltip,
  createResource,
  toast,
} from "frappe-ui";
import { PropType, computed, onMounted, ref } from "vue";

const authStore = useAuthStore();
const props = defineProps({
  activity: {
    type: Object as PropType<CommentActivity>,
    required: true,
  },
});
const { getUser } = useUserStore();
const { enableCommentReactions } = useConfigStore();

const { name, creation, content, commenter, commentedBy, attachments } =
  props.activity;

const { isMac } = useDevice();
const { isMobileView } = useScreenSize();
const isTicketMergedComment = computed(() => {
  const regex = /has been merged with ticket #\d+/;
  return regex.test(content);
});
const agentStore = useAgentStore();
const userMentions = computed(() => agentStore.dropdown ?? []);

const emit = defineEmits(["update"]);
const isConfirmingDelete = ref(false);
const editable = ref(false);
const _content = ref(content);

const emojiList = ["👍", "👎", "❤️", "🎉", "👀", "✅"];

const dropdownOptions = computed(() => [
  {
    label: "Edit",
    onClick: () => handleEditMode(),
    icon: "edit-2",
    condition: () => !isTicketMergedComment.value,
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteComment.submit(),
    isConfirmingDelete,
  }),
]);
// editor.commands.focus('end')

const reactions = ref<
  Array<{
    emoji: string;
    count: number;
    users: Array<{ user: string; full_name: string }>;
    current_user_reacted: boolean;
  }>
>([]);

const reactionsList = computed(() => reactions.value || []);

const fetchReactions = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_comment.hd_ticket_comment.get_reactions",
  makeParams: () => ({ comment: name }),
  auto: true,
  onSuccess(data) {
    reactions.value = data || [];
  },
});

const toggleReaction = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_comment.hd_ticket_comment.toggle_reaction",
  makeParams: (emoji: string) => ({ comment: name, emoji }),
  onSuccess() {
    fetchReactions.reload();
  },
});

function handleReaction(emoji: string) {
  const previousReaction = reactions.value.find(
    (r) => r.current_user_reacted && r.emoji !== emoji
  );
  if (previousReaction) {
    previousReaction.count = Math.max(0, previousReaction.count - 1);
    previousReaction.current_user_reacted = false;
  }

  const existingReaction = reactions.value.find((r) => r.emoji === emoji);
  if (existingReaction) {
    if (existingReaction.current_user_reacted) {
      existingReaction.count = Math.max(0, existingReaction.count - 1);
      existingReaction.current_user_reacted = false;
    } else {
      existingReaction.count += 1;
      existingReaction.current_user_reacted = true;
    }
  } else {
    reactions.value.push({
      emoji,
      count: 1,
      current_user_reacted: true,
      users: [
        {
          user: authStore.userId,
          full_name: getUser(authStore.userId).full_name,
        },
      ],
    });
  }

  toggleReaction.submit(emoji);
}

const commentBoxRef = ref(null);
const lastSavedContent = ref(content);
const commentBoxState = ref(content);

function handleEditMode() {
  editable.value = true;
  commentBoxState.value = _content.value;
}

function handleDiscard() {
  _content.value = commentBoxState.value;
  editable.value = false;
}

const deleteComment = createResource({
  url: "frappe.client.delete",
  makeParams: () => ({
    doctype: "HD Ticket Comment",
    name: name,
  }),
  onSuccess() {
    emit("update");
    toast.success(__("Comment deleted sucessfully."));
  },
});

function handleSaveComment() {
  if (lastSavedContent.value === _content.value) {
    editable.value = false;
    return;
  }
  if (isContentEmpty(_content.value)) {
    toast.error(__("Comment cannot be empty."));
    return;
  }

  updateComment.submit(
    {
      doctype: "HD Ticket Comment",
      name: name,
      fieldname: "content",
      value: _content.value,
    },
    {
      onSuccess: () => {
        editable.value = false;
        lastSavedContent.value = _content.value;
        emit("update");
        toast.success(__("Comment updated successfully."));
      },
    }
  );
}
onMounted(() => {
  // hack to persist the width of comment box to prevent it from resizing when the content is updated
  commentBoxRef.value.style.width = "0px";
});
</script>
