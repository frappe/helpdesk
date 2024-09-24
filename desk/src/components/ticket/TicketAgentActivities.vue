<template>
  <div class="h-screen py-3.5 comm-area px-3 lg:px-6">
    <ActivityHeader :title="title" />
    <div v-for="(activity, i) in activities" :key="activity.key">
      <!-- single activity -->
      <div class="flex gap-4 w-full">
        <div
          class="relative flex justify-center after:absolute after:left-[50%] after:top-0 after:-z-10 after:border-l after:border-gray-200"
          :class="[i != activities.length - 1 ? 'after:h-full' : 'after:h-4']"
        >
          <div
            class="z-10 flex h-7 w-7 items-center justify-center rounded-full bg-gray-100"
            :class="[
              activity.type === 'history' ? 'bg-white' : 'bg-gray-100',
              activity.type === 'comment' ? 'mt-0.5' : '',
              activity.type === 'email' ? 'mt-2' : '',
            ]"
          >
            <component
              :is="getActivityIcon(activity.type)"
              :class="[
                activity.type == 'history' ? 'text-gray-600' : 'text-gray-800',
              ]"
            />
          </div>
        </div>
        <div class="mb-4 w-full">
          <EmailArea
            v-if="activity.type === 'email'"
            :activity="activity"
            class="py-2 px-3"
            @reply="(e) => emit('email:reply', e)"
          />
          <CommentBox
            v-else-if="activity.type === 'comment'"
            :activity="activity"
            @update="() => emit('update')"
          />
          <HistoryBox v-else :activity="activity" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useElementVisibility } from "@vueuse/core";
import { DotIcon, EmailAtIcon, CommentIcon } from "@/components/icons";
import { EmailArea, CommentBox, HistoryBox } from "@/components";

defineProps({
  activities: {
    type: Array,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["email:reply", "update"]);

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
