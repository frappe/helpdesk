<template>
  <div class="flex flex-col comm-area">
    <div
      class="flex justify-between gap-3 border-t px-4 lg:px-10 py-4 md:py-2.5"
    >
      <div class="flex gap-1.5">
        <Button
          ref="sendEmailRef"
          variant="ghost"
          label="Reply"
          :class="[showEmailBox ? '!bg-gray-300 hover:!bg-gray-200' : '']"
          @click="toggleEmailBox()"
        >
          <template #prefix>
            <EmailIcon class="h-4" />
          </template>
        </Button>
        <Button
          variant="ghost"
          label="Comment"
          :class="[showCommentBox ? '!bg-gray-300 hover:!bg-gray-200' : '']"
          @click="toggleCommentBox()"
        >
          <template #prefix>
            <CommentIcon class="h-4" />
          </template>
        </Button>
      </div>
    </div>
    <div
      v-show="showCommentBox"
      @keydown.ctrl.enter.capture.stop="submitComment"
      @keydown.meta.enter.capture.stop="submitComment"
    >
      <CommentTextEditor
        ref="commentTextEditorRef"
        v-model="doc"
        :editable="showCommentBox"
        :doctype="doctype"
        placeholder="@John could you please look into this?"
        @submit="
          () => {
            showCommentBox = false;
            emit('update');
          }
        "
        @discard="
          () => {
            showCommentBox = false;
          }
        "
      />
    </div>
    <div
      v-show="showEmailBox"
      class="flex gap-1.5"
      @keydown.ctrl.enter.capture.stop="submitEmail"
      @keydown.meta.enter.capture.stop="submitEmail"
    >
      <EmailEditor
        ref="emailEditorRef"
        v-model="doc"
        v-model:content="content"
        placeholder="Hi John, we are looking into this issue."
        :to-emails="toEmails"
        :cc-emails="ccEmails"
        :bcc-emails="bccEmails"
        @submit="
          () => {
            showEmailBox = false;
            emit('update');
          }
        "
        @discard="
          () => {
            showEmailBox = false;
          }
        "
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

import { EmailEditor, CommentTextEditor } from "@/components";
import { EmailIcon, CommentIcon } from "@/components/icons/";

const emit = defineEmits(["update"]);
const content = defineModel("content");
const doc = defineModel();

const showEmailBox = ref(false);
const showCommentBox = ref(false);

const emailEditorRef = ref(null);
const commentTextEditorRef = ref(null);

function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false;
  }
  showEmailBox.value = !showEmailBox.value;
}

function toggleCommentBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false;
  }
  showCommentBox.value = !showCommentBox.value;
}

function submitEmail() {
  emailEditorRef.value.submitMail();
  emit("update");
}

function submitComment() {
  commentTextEditorRef.value.submitComment();
  emit("update");
}

function replyToEmail(data: object) {
  showEmailBox.value = true;
  emailEditorRef.value.addToReply(
    data.content,
    data.to?.split(","),
    data.cc?.split(","),
    data.bcc?.split(",")
  );
}

function forwardEmail(data: object) {
  showEmailBox.value = true;
  emailEditorRef.value.addToForward(
    data.content,
    data.subject,
    data.attachments
  );
}

const props = defineProps({
  doctype: {
    type: String,
    default: "HD Ticket",
  },
  toEmails: {
    type: Array,
    default: () => [],
  },
  ccEmails: {
    type: Array,
    default: () => [],
  },
  bccEmails: {
    type: Array,
    default: () => [],
  },
});

defineExpose({
  replyToEmail,
  forwardEmail,
  toggleEmailBox,
  toggleCommentBox,
  editor: emailEditorRef,
});
</script>

<style>
@media screen and (max-width: 640px) {
  .comm-area {
    width: 100vw;
  }
}
</style>
