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
      v-model="doc"
      v-model:attachments="attachments"
      :editable="showCommentBox"
      :doctype="doctype"
      placeholder="Add a comment..."
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
      ref="newEmailEditor"
      v-model:content="content"
      v-model:attachments="attachments"
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
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import EmailIcon from "@/components/icons/EmailIcon.vue";
import CommentIcon from "@/components/icons/CommentIcon.vue";
import { useAuthStore } from "@/stores/auth";
import { EmailEditor, CommentTextEditor } from "@/components";
import { ref, defineModel, nextTick } from "vue";

const authStore = useAuthStore();
const content = defineModel("content");
const showEmailBox = ref(false);
const showCommentBox = ref(false);
const doc = defineModel();
const attachments = ref([]);
const newEmailEditor = ref(null);
const emit = defineEmits(["update"]);

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
</script>
