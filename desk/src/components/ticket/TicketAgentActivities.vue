<template>
  <div v-for="activity in activities" :key="activity.key">
    <div class="flex flex-row gap-4 px-10">
      <div
        v-show="activity.type === 'email' || type === 'all'"
        class="activity relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-gray-200"
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
      <CommentBox
        v-else-if="activity.type === 'comment' && type === 'all'"
        v-bind="activity"
      />
      <HistoryBox v-else-if="type === 'all'" v-bind="activity" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { DotIcon, EmailAtIcon, CommentIcon } from "@/components/icons";
import { EmailBox, CommentBox, HistoryBox } from "@/components";

defineProps({
  activities: {
    type: Array,
    required: true,
  },
  type: {
    type: String,
    default: "all",
  },
});

function getActivityIcon(type) {
  if (type === "email") return EmailAtIcon;
  else if (type === "comment") return CommentIcon;
  else return DotIcon;
}
</script>

<style scoped>
.activity::before {
  content: var(--tw-content);
  height: 1rem /* 16px */;
}
.activity:last-of-type::before {
  content: var(--tw-content);
  height: 100%;
}
</style>
