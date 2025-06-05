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
    <div class="rounded bg-gray-50 px-4 py-3">
      <TextEditor
        ref="editorRef"
        :editor-class="[
          'prose-f shrink text-p-sm transition-all duration-300 ease-in-out block w-full content',
          getFontFamily(_content),
        ]"
        :content="_content"
        :editable="editable"
        :bubble-menu="textEditorMenuButtons"
        @change="(event:string) => {_content = event}"
      >
        <template #bottom v-if="editable">
          <div class="flex flex-row-reverse gap-2">
            <Button label="Save" @click="handleSaveComment" variant="solid" />
            <Button label="Discard" @click="handleDiscard" />
          </div>
        </template>
      </TextEditor>
      <div class="flex flex-wrap gap-2" v-if="!editable">
        <AttachmentItem
          v-for="a in attachments"
          :key="a.file_url"
          :label="a.file_name"
          :url="a.file_url"
        />
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
import { useAuthStore } from "@/stores/auth";
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
  TextEditor,
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

// HTML refs
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
