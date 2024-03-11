<template>
  <div class="flex items-center justify-between px-10 py-5 text-lg font-medium">
    <div class="flex h-7 items-center text-xl font-semibold text-gray-800">
      {{ title }}
    </div>
  </div>
  <div v-for="(activity, i) in activities" :key="activity.key">
    <div class="flex flex-row gap-4 px-10">
      <div
        class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-gray-200"
        :class="[i != activities.length - 1 ? 'before:h-full' : 'before:h-4']"
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
import { defineModel } from "vue";
import { DotIcon, EmailAtIcon, CommentIcon } from "@/components/icons";
import { EmailBox, CommentBox, HistoryBox } from "@/components";

const props = defineProps({
  title: {
    type: String,
    default: "Activity",
  },
});

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

let activities;

if (props.title === "Emails") {
  activities = emailProps;
} else {
  activities = [...emailProps, ...commentProps, ...historyProps];
}

activities = activities.sort(
  (a, b) => new Date(a.creation) - new Date(b.creation)
);
</script>
