
<template>
  <div class="flex items-center justify-between px-5 py-3 border-b flex-shrink-0">
    <h3 class="text-base font-semibold text-ink-gray-9">{{ title }}</h3>
      
    <Button
      v-if="title === __('Tasks')"
      variant="solid"
      class="bg-gray-900 text-white hover:bg-gray-800 transition-colors"
      @click="showNewTaskModal = true"
    >
      <template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
      {{ __("New") }}
    </Button>
  </div>
  
  <TaskboxEditor
    v-model="showNewTaskModal"
    :ticket-id="resolvedTicketId"
    @submit="
      () => {
        showNewTaskModal = false;
        emit('update');
      }
    "
  />

  <FadedScrollableDiv
    class="flex flex-col flex-1 overflow-y-auto"
    :mask-length="20"
  >
    <div v-if="localActivities.length" class="activities flex-1 h-full mt-0.5 px-6 md:px-5">
      <div
        v-for="(activity, i) in localActivities"
        :key="activity.key"
        class="activity mt-2"
        tabindex="0"
      >
        <div class="w-full flex flex-col">
          <div
            class="mb-4 flex w-full"
            :class="[
              i === localActivities.length - 1 && 'mb-5',
              !['email', 'feedback', 'call', 'comment', 'task'].includes(
                activity.type
              ) && 'mt-[2px]',
            ]"
          >
            <EmailArea
              v-if="activity.type === 'email'"
              :activity="activity"
              :show-split-option="
                !activity.isFirstEmail && ticketStatus !== 'Closed'
              "
              class="py-2 px-3 flex-1 w-full"
              @reply="(e) => emit('email:reply', e)"
            />
            <CommentBox
              v-else-if="activity.type === 'comment'"
              :activity="activity"
              class="flex-1 w-full"
              @update="() => emit('update')"
            />
            <div v-else-if="activity.type === 'task'" class="flex-1 w-full">
              <Taskbox
                :activity="activity"
                :reload-tasks="() => emit('update')"
                @update="() => emit('update')"
              />
            </div>
            <HistoryBox
              v-else-if="activity.type === 'call'"
              :activity="activity"
              class="flex-1 w-full"
            />
            <FeedbackBox
              :activity="activity"
              v-else-if="activity.type === 'feedback'"
              class="flex-1 w-full"
            />
            <HistoryBox 
              v-else 
              :activity="activity" 
              class="flex-1 w-full"
            />
          </div>
        </div>
      </div>
    </div>
    
    <div
      v-else
      class="h-screen flex flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <component :is="emptyTextIcon" class="h-7.5 w-7.5" />
      <span class="text-lg font-medium text-ink-gray-8">{{
        __(emptyText)
      }}</span>
    </div>
  </FadedScrollableDiv>
</template>

<script setup lang="ts">
import { computed, h, inject, nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Avatar, Button, FeatherIcon } from "frappe-ui";
import { FadedScrollableDiv } from "@/components";
import {
  ActivityIcon,
  CommentIcon,
  DotIcon,
  EmailIcon,
  PhoneIcon,
  TaskIcon,
} from "@/components/icons";
import { useUserStore } from "@/stores/user";
import { TicketActivity } from "@/types";
import { isElementInViewport } from "@/utils";
import { __ } from "@/translation";
import FeedbackBox from "../ticket-agent/FeedbackBox.vue";
import CommentBox from "@/components/CommentBox.vue";
import EmailArea from "@/components/EmailArea.vue";
import HistoryBox from "@/components/HistoryBox.vue";
import Taskbox from "@/components/Taskbox.vue";
import TaskboxEditor from "@/components/TaskboxEditor.vue";

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
  ticketId: {
    type: [String, Number],
    default: "",
  },
});

const emit = defineEmits(["email:reply", "update", "new-email"]);

const route = useRoute();
const router = useRouter();
const { getUser } = useUserStore();

const showNewTaskModal = ref(false);

const injectedTicketId = inject<string | number>("ticketId", "");
const resolvedTicketId = computed(() =>
  String(props.ticketId || injectedTicketId || "").trim()
);

// Decouples tab viewing filter constraints
const localActivities = computed(() => {
  if (props.title === __("Activity")) {
    return props.activities.filter((activity) => activity.type !== "task");
  }
  return props.activities;
});

const emptyText = computed(() => {
  if (props.title === "Emails") return "No email communications";
  if (props.title === "Comments") return "No comments found";
  if (props.title === "Calls") return "No calls made";
  if (props.title === "Tasks") return "No tasks found";
  return "No activity found";
});

const emptyTextIcon = computed(() => {
  let icon: any = ActivityIcon;
  if (props.title === __("Emails")) {
    icon = EmailIcon;
  } else if (props.title === __("Comments")) {
    icon = CommentIcon;
  } else if (props.title === __("Calls")) {
    icon = PhoneIcon;
  } else if (props.title === __("Tasks")) {
    icon = TaskIcon;
  }
  return h(icon, { class: "text-ink-gray-4" });
});

onMounted(() => {
  nextTick(() => {
    document.querySelector(".activity")?.focus();
  });
});

function scrollToLatestActivity() {
  if (route.hash) {
    scrollToHash();
    return;
  }
  setTimeout(() => {
    const elements = document.getElementsByClassName("activity");
    const el = elements[elements.length - 1] as HTMLElement;
    if (el && !isElementInViewport(el)) {
      (el as any).scrollIntoViewIfNeeded();
      el.focus();
    }
  }, 500);
}

function scrollToHash() {
  const hash = route.hash;
  if (!hash) return;
  nextTick(() => {
    setTimeout(() => {
      const element = document.getElementById(hash.substring(1));
      if (element) {
        (element as any).scrollIntoViewIfNeeded();
        element.classList.add("bg-yellow-100");
        setTimeout(() => {
          element.classList.remove("bg-yellow-100");
          router.replace({ hash: "" });
        }, 2000);
      }
    }, 1000);
  });
}

watch(
  () => route.hash,
  () => {
    scrollToLatestActivity();
  }
);

watch(
  () => props.title,
  () => {
    scrollToLatestActivity();
  },
  { immediate: true }
);

defineExpose({
  scrollToLatestActivity,
});
</script>
<style scoped>
.activity:focus {
  outline: none;
}
</style>