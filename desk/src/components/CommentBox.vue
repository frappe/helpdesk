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
      <div class="flex items-center">
        <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
          <span class="pl-0.5 text-sm text-gray-600">
            {{ timeAgo(creation) }}
          </span>
        </Tooltip>
        <div v-if="authStore.userId === commentedBy">
          <Dropdown
            :options="[{ label: 'Delete', onClick: () => (showDialog = true) }]"
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
    <TextEditor
      ref="editorRef"
      :editor-class="'prose-f shrink rounded bg-gray-50 px-4 py-3 text-p-sm transition-all duration-300 ease-in-out block w-full '"
      :content="content"
      :editable="false"
      @change="(event:string) => {content = event}"
    >
      <template #bottom v-if="false">
        <TextEditorFixedMenu
          class="-ml-1 overflow-x-auto w-full"
          :buttons="textEditorMenuButtons"
        />
      </template>
    </TextEditor>
    <!-- <div
      class="prose-f grow cursor-pointer rounded bg-gray-50 px-4 py-3 text-base leading-6 transition-all duration-300 ease-in-out"
    >
      <iframe :srcdoc="content" class="prose-f block w-full h-fit" />
    </div> -->
    <!-- <div class="flex flex-wrap gap-2">
      <AttachmentItem
        v-for="a in attachments"
        :key="a.file_url"
        :label="a.file_name"
        :url="a.file_url"
      />
    </div> -->
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
import { ref, PropType } from "vue";
import {
  Dropdown,
  createResource,
  Dialog,
  Avatar,
  TextEditor,
  TextEditorFixedMenu,
} from "frappe-ui";
// import { EmailContent } from "@/components/EmailContent.vue";
import {
  dateFormat,
  timeAgo,
  dateTooltipFormat,
  createToast,
  textEditorMenuButtons,
} from "@/utils";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { CommentActivity } from "@/types";
import { onMounted } from "vue";
const authStore = useAuthStore();
const props = defineProps({
  activity: {
    type: Object as PropType<CommentActivity>,
    required: true,
  },
});
const { getUser } = useUserStore();

const { name, creation, content, commenter, commentedBy } = props.activity;

const emit = defineEmits(["update"]);
const showDialog = ref(false);
const commentBoxRef = ref(null);

onMounted(() => {
  commentBoxRef.value.style.width = "0px";
});

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
</script>
