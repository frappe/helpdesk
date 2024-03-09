<template>
  <div class="flex items-center justify-between px-10 py-5 text-lg font-medium">
    <div class="flex h-7 items-center text-xl font-semibold text-gray-800">
      {{ title }}
    </div>
  </div>
  <div v-for="activity in activities" :key="activity.key">
    <div class="flex flex-row gap-4 px-10">
      <div
        class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-gray-200"
        :class="[
          'before:h-full',
          'after:translate-y-[calc(-50% - 4px)] after:absolute after:bottom-9 after:left-[50%] after:top-0 after:-z-10 after:w-8 after:rounded-bl-xl after:border-b after:border-l after:border-gray-200',
        ]"
      >
        <div
          class="z-10 mt-3 flex h-7 w-7 items-center justify-center rounded-full bg-gray-100"
          :class="{
            'bg-white': activity.type === 'history',
          }"
        >
          <component
            :is="getActivityIcon(activity.type)"
            :class="'text-gray-800'"
          />
        </div>
      </div>
      <EmailBox v-if="activity.type === 'email'" v-bind="activity" />
      <CommentBox v-if="activity.type === 'comment'" v-bind="activity" />
      <HistoryBox v-if="activity.type === 'history'" v-bind="activity" />
    </div>
  </div>
</template>

<script setup lang="ts">
import EmailAtIcon from "@/components/icons/EmailAtIcon.vue";
import CommentIcon from "@/components/icons/CommentIcon.vue";
import DotIcon from "./icons/DotIcon.vue";
import { defineModel } from "vue";
import { EmailBox, CommentBox, HistoryBox } from "@/components";

const doc = defineModel();
const emails = doc.value.data.communications;
const comments = doc.value.data.comments;
const history = doc.value.data.history;
const views = doc.value.data.views;

function getActivityIcon(type) {
  if (type === "email") return EmailAtIcon;
  else if (type === "comment") return CommentIcon;
  else return DotIcon;
}

const emailProps = emails.map((email) => {
  return {
    type: "email",
    key: email.creation,
    sender: { name: email.user.email, full_name: email.user.name },
    to: email.recipients,
    cc: email.cc,
    bcc: email.bcc,
    creation: email.creation,
    subject: email.subject,
    attachments: email.attachments,
    content: email.content,
  };
});

const commentProps = comments.map((comment) => {
  return {
    type: "comment",
    key: comment.creation,
    commenter: comment.user.name,
    creation: comment.creation,
    content: comment.content,
  };
});

const historyProps = [...history, ...views].map((h) => {
  return {
    type: "history",
    key: h.creation,
    content: h.action ? h.action : "viewed this",
    creation: h.creation,
    user: h.user.name + " ",
  };
});

const activities = [...emailProps, ...commentProps, ...historyProps].sort(
  (a, b) => new Date(a.creation) - new Date(b.creation)
);

defineProps({
  title: {
    type: String,
    default: "Activity",
  },
});
</script>
