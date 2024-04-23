<template>
  <div class="h-screen overflow-y-auto">
    <div
      v-for="(activity, i) in activities"
      :key="activity.key"
      class="activity"
    >
      <div class="flex gap-4 px-10">
        <div
          class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-gray-200"
        >
          <div
            class="z-10 mt-3 flex h-7 w-7 items-center justify-center rounded-full bg-gray-100"
            :class="[
              i != activities.length - 1 ? 'before:h-full' : 'before:h-4',
              activity.type === 'history' ? 'bg-white' : 'bg-gray-100',
            ]"
          >
            <component
              :is="getActivityIcon(activity.type)"
              :class="'text-gray-800'"
            />
          </div>
        </div>
        <div class="mt-4 w-full">
          <EmailBox v-if="activity.type === 'email'" v-bind="activity" />
          <CommentBox
            v-else-if="activity.type === 'comment'"
            v-bind="activity"
          />
          <HistoryBox v-else v-bind="activity" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useElementVisibility } from "@vueuse/core";
import { DotIcon, EmailAtIcon, CommentIcon } from "@/components/icons";
import { EmailBox, CommentBox, HistoryBox } from "@/components";

defineProps({
  activities: {
    type: Array,
    required: true,
  },
});

function getActivityIcon(type) {
  if (type === "email") return EmailAtIcon;
  else if (type === "comment") return CommentIcon;
  else return DotIcon;
}

function scrollToLatestActivity() {
  setTimeout(() => {
    let el;
    let e = document.getElementsByClassName("activity");
    el = e[e.length - 1];
    if (el && !useElementVisibility(el).value) {
      el.scrollIntoView({ behavior: "smooth" });
      el.focus();
    }
  }, 500);
}

defineExpose({
  scrollToLatestActivity,
});
</script>
