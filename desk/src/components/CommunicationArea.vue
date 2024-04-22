<template>
  <div class="flex justify-between gap-3 border-t px-10 py-2.5">
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
    <div v-show="showEmailBox" class="flex gap-1.5">
      <Button
        label="CC"
        :class="[false ? 'bg-gray-300 hover:bg-gray-200' : '']"
        @click="toggleCC()"
      />
      <Button
        label="BCC"
        :class="[false ? 'bg-gray-300 hover:bg-gray-200' : '']"
        @click="toggleBCC()"
      />
    </div>
  </div>
  <div v-show="showCommentBox">
    <CommentTextEditor
      ref="newCommentEditor"
      v-model:content="newComment"
      v-model="doc"
      v-model:attachments="attachments"
      :submit-button-props="{
        variant: 'solid',
        onClick: submitComment,
        disabled: commentEmpty,
      }"
      :discard-button-props="{
        onClick: () => {
          showCommentBox = false;
          newComment = '';
        },
      }"
      :editable="showCommentBox"
      :doctype="doctype"
      placeholder="Add a comment..."
    />
  </div>
  <div
    v-show="showEmailBox"
    class="flex gap-1.5"
    @keydown.ctrl.enter.capture.stop="submitEmail"
    @keydown.meta.enter.capture.stop="submitEmail"
  >
    <EmailEditor
      ref="newEmailEditor"
      v-model:content="content"
      v-model:attachments="attachments"
      :to-emails="toEmails"
      :cc-emails="ccEmails"
      :bcc-emails="bccEmails"
      :submit-button-props="{
        variant: 'solid',
        onClick: submitEmail,
        disabled: emailEmpty,
      }"
      :discard-button-props="{
        onClick: () => {
          showEmailBox = false;
          newEmailEditor.ccEmails = [];
          newEmailEditor.bccEmails = [];
          newEmailEditor.cc = false;
          newEmailEditor.bcc = false;
        },
      }"
    />
  </div>
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import EmailIcon from "@/components/icons/EmailIcon.vue";
import CommentIcon from "@/components/icons/CommentIcon.vue";
import { useAuthStore } from "@/stores/auth";
import { EmailEditor, CommentTextEditor } from "@/components";
import { computed, ref, defineModel, nextTick } from "vue";
import { useStorage } from "@vueuse/core";

const authStore = useAuthStore();
const content = defineModel("content");
const showEmailBox = ref(false);
const showCommentBox = ref(false);
const doc = defineModel();
const attachments = ref([]);
const newEmailEditor = ref(null);

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

function toggleCC() {
  newEmailEditor.value.cc = !newEmailEditor.value.cc;
  newEmailEditor.value.cc &&
    nextTick(() => {
      newEmailEditor.value.ccInput.setFocus();
    });
}

function toggleBCC() {
  newEmailEditor.value.bcc = !newEmailEditor.value.bcc;
  newEmailEditor.value.bcc &&
    nextTick(() => {
      newEmailEditor.value.bccInput.setFocus();
    });
}

const newEmail = useStorage("emailBoxContent", "");
const newComment = useStorage("commentBoxContent", "");

const commentEmpty = computed(() => {
  return !newComment.value || newComment.value === "<p></p>";
});

const emailEmpty = computed(() => {
  return !newEmail.value || newEmail.value === "<p></p>";
});

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
  content: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["scroll"]);

const sendMail = createResource({
  url: "run_doc_method",
  makeParams: () => ({
    dt: "HD Ticket",
    dn: doc.value.data.name,
    method: "reply_via_agent",
    args: {
      attachments: attachments.value.map((x) => x.name),
      cc: (newEmailEditor.value.ccEmails || []).join(","),
      bcc: (newEmailEditor.value.bccEmails || []).join(","),
      message: newEmail.value,
    },
  }),
  // onSuccess: () => {
  //   clear();
  //   emitter.emit("update:ticket");
  // },
});

async function submitEmail() {
  if (emailEmpty.value) return;
  showEmailBox.value = false;
  sendMail.submit();
  newEmail.value = "";
  emit("scroll");
}

async function sendComment() {
  const comment = createResource({
    url: "run_doc_method",
    makeParams: () => ({
      dt: "HD Ticket",
      dn: doc.value.data.name,
      method: "new_comment",
      args: {
        content: newComment.value,
      },
    }),
  });

  comment.submit();
}

async function submitComment() {
  if (commentEmpty.value) return;
  showCommentBox.value = false;
  await sendComment();
  newComment.value = "";
  emit("scroll");
}
</script>
