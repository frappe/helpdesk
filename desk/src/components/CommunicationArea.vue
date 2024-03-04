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
    <div v-if="showEmailBox" class="flex gap-1.5">
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
  <div
    v-show="showEmailBox"
    class="flex gap-1.5"
    @keydown.ctrl.enter.capture.stop="submitEmail"
    @keydown.meta.enter.capture.stop="submitEmail"
  >
    <EmailEditor
      ref="newEmailEditor"
      v-model:content="newEmail"
      v-model:attachments="attachments"
      v-model="doc.data"
      :submit-button-props="{
        variant: 'solid',
        onClick: submitEmail,
        disabled: emailEmpty,
      }"
      :discard-button-props="{
        onClick: () => {
          showEmailBox = false;
          // newEmailEditor.subject = subject; //TODO
          newEmailEditor.toEmails = doc.data.email ? [doc.data.email] : [];
          newEmailEditor.ccEmails = [];
          newEmailEditor.bccEmails = [];
          newEmailEditor.cc = false;
          newEmailEditor.bcc = false;
          newEmail = '';
        },
      }"
    />
  </div>
</template>

<script setup lang="ts">
import { call } from "frappe-ui";
import EmailIcon from "@/components/icons/EmailIcon.vue";
import CommentIcon from "@/components/icons/CommentIcon.vue";
import { useAuthStore } from "@/stores/auth";
import { EmailEditor } from "@/components";
import { File } from "@/types";
import { computed, ref, defineModel, nextTick, watch, defineProps } from "vue";
import { useStorage } from "@vueuse/core";

const authStore = useAuthStore();
const showEmailBox = ref(false);
const showCommentBox = ref(false);
const doc = defineModel();
const attachments = ref([]);
const newEmailEditor = ref(null);

const newEmail = useStorage("emailBoxContent", "");

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

const emailEmpty = computed(() => {
  return !newEmail.value || newEmail.value === "<p></p>";
});

const reload = defineModel("reload");

const props = defineProps({
  doctype: {
    type: String,
    default: "HD Ticket",
  },
});

const emit = defineEmits(["scroll"]);

async function sendMail() {
  let recipients = newEmailEditor.value.toEmails;
  let subject = newEmailEditor.value.subject;
  let cc = newEmailEditor.value.ccEmails || [];
  let bcc = newEmailEditor.value.bccEmails || [];
  await call("frappe.core.doctype.communication.email.make", {
    recipients: recipients.join(", "),
    attachments: attachments.value.map((x) => x.name),
    cc: cc.join(", "),
    bcc: bcc.join(", "),
    subject: subject,
    content: newEmail.value,
    doctype: props.doctype,
    name: doc.value.data.name,
    send_email: 1,
    sender: authStore.userId,
    sender_full_name: authStore.userName || undefined,
  });
}

async function submitEmail() {
  if (emailEmpty.value) return;
  showEmailBox.value = false;
  await sendMail();
  newEmail.value = "";
  reload.value = true;
  emit("scroll");
}
</script>
