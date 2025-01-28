<template>
  <div class="flex-col text-base flex-1" ref="commentBoxRef">
    <div class="mb-1 ml-0.5 flex items-center justify-between">
      <div class="text-gray-600 flex items-center gap-2">
        <Avatar
          size="sm"
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
            :options="[
              {
                label: 'Edit',
                onClick: () => handleEditMode(),
                icon: 'edit-2',
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
        :editor-class="'prose-f shrink  text-p-sm transition-all duration-300 ease-in-out block w-full content'"
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
import { ref, PropType, onMounted } from "vue";
import {
  Dropdown,
  createResource,
  Dialog,
  Avatar,
  TextEditor,
} from "frappe-ui";
import {
  dateFormat,
  timeAgo,
  dateTooltipFormat,
  createToast,
  textEditorMenuButtons,
  isContentEmpty,
} from "@/utils";
import { AttachmentItem } from "@/components";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { CommentActivity } from "@/types";
import { updateRes as updateComment } from "@/stores/knowledgeBase";
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
    createToast({
      title: "Comment deleted",
      icon: "check",
      iconClasses: "text-green-500",
    });
  },
});

function handleSaveComment() {
  if (content === _content.value) {
    editable.value = false;
    return;
  }
  if (isContentEmpty(_content.value)) {
    createToast({
      title: "Comment cannot be empty",
      icon: "x",
      iconClasses: "text-red-600",
    });
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
        createToast({
          title: "Comment updated",
          icon: "check",
          iconClasses: "text-green-500",
        });
      },
    }
  );
}

onMounted(() => {
  commentBoxRef.value.style.width = "0px";
});
</script>
