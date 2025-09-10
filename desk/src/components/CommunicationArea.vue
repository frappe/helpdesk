<template>
  <div class="comm-area">
    <div
      class="flex justify-between gap-3 border-t px-6 md:px-10 py-4 md:py-2.5"
    >
      <div class="flex gap-1.5 items-center">
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
        <TypingIndicator :ticketId="ticketId" />
      </div>
    </div>
    <div
      v-show="showEmailBox"
      class="flex gap-1.5 flex-1"
      @keydown.ctrl.enter.capture.stop="submitEmail"
      @keydown.meta.enter.capture.stop="submitEmail"
    >
      <EmailEditor
        ref="emailEditorRef"
        :label="
          isMobileView ? 'Send' : isMac ? 'Send (⌘ + ⏎)' : 'Send (Ctrl + ⏎)'
        "
        v-model:content="content"
        placeholder="Hi John, we are looking into this issue."
        :ticketId="ticketId"
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
    <div
      v-show="showCommentBox"
      @keydown.ctrl.enter.capture.stop="submitComment"
      @keydown.meta.enter.capture.stop="submitComment"
    >
      <CommentTextEditor
        ref="commentTextEditorRef"
        :label="
          isMobileView
            ? 'Comment'
            : isMac
            ? 'Comment (⌘ + ⏎)'
            : 'Comment (Ctrl + ⏎)'
        "
        :ticketId="ticketId"
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
  </div>
</template>

<script setup lang="ts">
import { CommentTextEditor, EmailEditor, TypingIndicator } from "@/components";
import { CommentIcon, EmailIcon } from "@/components/icons/";
import { useDevice } from "@/composables";
import { useScreenSize } from "@/composables/screen";
import { showCommentBox, showEmailBox } from "@/pages/ticket/modalStates";
import { ref, watch } from "vue";

const emit = defineEmits(["update"]);
const content = defineModel("content");
const { isMac } = useDevice();
const { isMobileView } = useScreenSize();
let doc = defineModel();
// let doc = inject(TicketSymbol)?.value.doc
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
  if (emailEditorRef.value.submitMail()) {
    emit("update");
  }
}

function submitComment() {
  if (commentTextEditorRef.value.submitComment()) {
    emit("update");
  }
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

const props = defineProps({
  doctype: {
    type: String,
    default: "HD Ticket",
  },
  ticketId: {
    type: String,
    default: null,
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

watch(
  () => showEmailBox.value,
  (value) => {
    if (value) {
      emailEditorRef.value?.editor?.commands?.focus();
    }
  }
);

watch(
  () => showCommentBox.value,
  (value) => {
    if (value) {
      commentTextEditorRef.value?.editor?.commands?.focus();
    }
  }
);

defineExpose({
  replyToEmail,
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
