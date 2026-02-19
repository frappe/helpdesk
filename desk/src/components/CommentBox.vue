<template>
  <div class="flex-col text-base flex-1" ref="commentBoxRef">
    <div class="mb-1 ml-0.5 flex items-center justify-between">
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
          <span> added a</span>
          <span class="max-w-xs truncate font-medium text-gray-800">
            comment
          </span>
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
            :options="[
              {
                label: 'Edit',
                onClick: () => handleEditMode(),
                icon: 'edit-2',
                condition: () => !isTicketMergedComment,
              },
              {
                label: 'Delete',
                onClick: () => (showDialog = true),
                icon: 'trash-2',
              },
            ]"
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
      class="rounded bg-gray-50 transition-colors px-4 py-3"
    >
      <TextEditor
        ref="editorRef"
        :editor-class="[
          'prose-f shrink text-p-sm transition-all duration-300 ease-in-out block w-full content',
          getFontFamily(_content),
        ]"
        :content="_content"
        :editable="editable"
        :bubble-menu="textEditorMenuButtons"
        :mentions="[]"
        @change="(event:string) => {_content = event}"
      >
        <template #bottom v-if="editable">
          <div class="flex flex-row-reverse gap-2">
            <Button label="Save" @click="handleSaveComment" variant="solid" />
            <Button label="Discard" @click="handleDiscard" />
          </div>
        </template>
      </TextEditor>
      <div
        class="flex flex-wrap gap-2"
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
        class="flex items-center gap-2 mt-2"
        v-if="!editable && enableCommentReactions"
      >
        <Popover>
          <template #target="{ togglePopover }">
            <button
              class="flex h-full items-center justify-center rounded-full bg-surface-gray-2 px-2 py-1 text-ink-gray-6 transition hover:bg-surface-gray-3"
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
  <Dialog
    v-model="showDialog"
    :options="{
      title: 'Delete Comment',
      message: 'Are you sure you want to confirm this action?',
      actions: [
        { label: 'Cancel', onClick: () => (showDialog = false) },
        {
          label: 'Delete',
          onClick: () => deleteComment.submit(),
          variant: 'solid',
        },
      ],
    }"
  />
</template>

<script setup lang="ts">
import { AttachmentItem } from "@/components";
import ReactionIcon from "@/components/icons/ReactionIcon.vue";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { updateRes as updateComment } from "@/stores/knowledgeBase";
import { useUserStore } from "@/stores/user";
import { CommentActivity } from "@/types";
import {
  dateFormat,
  dateTooltipFormat,
  getFontFamily,
  isContentEmpty,
  textEditorMenuButtons,
  timeAgo,
} from "@/utils";
import {
  Avatar,
  Dialog,
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

const isTicketMergedComment = computed(() => {
  const regex = /has been merged with ticket #\d+/;
  return regex.test(content);
});

const emit = defineEmits(["update"]);
const showDialog = ref(false);
const editable = ref(false);
const _content = ref(content);

const emojiList = ["👍", "👎", "❤️", "🎉", "👀", "✅"];

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
  toggleReaction.submit(emoji);
}

const commentBoxRef = ref(null);
const editorRef = ref(null);

function handleEditMode() {
  editable.value = true;
  editorRef.value.editor.chain().focus("start");
}

function handleDiscard() {
  _content.value = content;
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
    showDialog.value = false;
    toast.success("Comment deleted");
  },
});

function handleSaveComment() {
  if (content === _content.value) {
    editable.value = false;
    return;
  }
  if (isContentEmpty(_content.value)) {
    toast.error("Comment cannot be empty");
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
        emit("update");
        toast.success("Comment updated");
      },
    }
  );
}

onMounted(() => {
  commentBoxRef.value.style.width = "0px";
});
</script>
