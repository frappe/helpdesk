<template>
  <ActivityHeader :title="title" />
  <FadedScrollableDiv class="flex flex-col flex-1 overflow-y-scroll">
    <div v-if="activities.length" class="activities flex-1 h-full mt-1">
      <div
        v-for="(activity, i) in activities"
        :key="activity.key"
        class="activity"
      >
        <!-- single activity -->
        <div
          class="w-full px-6 md:px-10 grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4"
        >
          <div
            class="relative flex justify-center after:absolute after:left-[50%] after:top-2 after:-z-10 after:border-l after:border-gray-200"
            :class="[i != activities.length - 1 ? 'after:h-full' : 'after:h-4']"
          >
            <div
              class="z-10 flex h-7 w-7 items-center justify-center rounded-full bg-white"
              :class="[activity.type === 'email' && 'mt-2']"
            >
              <Avatar
                v-if="activity.type === 'email'"
                size="lg"
                :label="activity.sender?.full_name"
                :image="getUser(activity.sender?.name).user_image"
                class="bg-white absolute left-[1px]"
              />
              <CommentIcon
                v-else-if="activity.type === 'comment'"
                class="text-gray-600 absolute left-[7.5px]"
              />
              <DotIcon v-else class="text-gray-600 absolute left-[7.5px]" />
            </div>
          </div>
          <div
            class="mb-4 flex flex-1"
            :class="[i == activities.length - 1 && 'mb-5']"
          >
            <EmailArea
              v-if="activity.type === 'email'"
              :activity="activity"
              :show-split-option="
                !activity.isFirstEmail && ticketStatus !== 'Closed'
              "
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
    <div
      v-else
      class="h-full flex flex-col items-center justify-center gap-3 text-xl font-medium text-gray-500"
    >
      <component :is="emptyTextIcon" class="h-10 w-10" />
      <span>{{ emptyText }}</span>
      <Button
        v-if="title == 'Emails'"
        label="New Email"
        @click="communicationAreaRef.toggleEmailBox()"
      />
      <Button
        v-else-if="title == 'Comments'"
        label="New Comment"
        @click="communicationAreaRef.toggleCommentBox()"
      />
    </div>
  </FadedScrollableDiv>
</template>

<script setup lang="ts">
import {
  CommentBox,
  EmailArea,
  FadedScrollableDiv,
  HistoryBox,
} from "@/components";
import {
  ActivityIcon,
  CommentIcon,
  DotIcon,
  EmailIcon,
} from "@/components/icons";
import { useUserStore } from "@/stores/user";
import { TicketActivity } from "@/types";
import { useElementVisibility } from "@vueuse/core";
import { Avatar } from "frappe-ui";
import { PropType, Ref, computed, h, inject, onMounted, watch } from "vue";
const props = defineProps({
  activities: {
    type: Array as PropType<TicketActivity[]>,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  ticketStatus: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["email:reply", "update"]);

const { getUser } = useUserStore();
const communicationAreaRef: Ref = inject("communicationArea");

const emptyText = computed(() => {
  let text = "No Activities";
  if (props.title == "Emails") {
    text = "No Email Communications";
  } else if (props.title == "Comments") {
    text = "No Comments";
    return text;
  }
});

const emptyTextIcon = computed(() => {
  let icon = ActivityIcon;
  if (props.title == "Emails") {
    icon = EmailIcon;
  } else if (props.title == "Comments") {
    icon = CommentIcon;
  }
  return h(icon, { class: "text-gray-500" });
});

function scrollToLatestActivity() {
  setTimeout(() => {
    let el;
    let e = document.getElementsByClassName("activity");
    el = e[e.length - 1];
    if (el && !useElementVisibility(el).value) {
      el.scrollIntoView();
      el.focus();
    }
  }, 500);
}

defineExpose({
  scrollToLatestActivity,
});

onMounted(() => {
  scrollToLatestActivity();
});

watch(
  () => props.title,
  () => {
    scrollToLatestActivity();
  }
);
</script>
