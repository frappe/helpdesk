<template>
  <ActivityHeader
    :title="title"
    @new-task="showTaskEditor = !showTaskEditor"
    @new-email="emit('new-email')"
  />
  <TaskboxEditor
    v-if="showTaskEditor && title === __('Tasks')"
    :ticket-id="ticketId"
    @submit="handleTaskCreated"
    @discard="showTaskEditor = false"
  />
  <FadedScrollableDiv
    class="flex flex-col flex-1 overflow-y-auto"
    :mask-length="20"
  >
    <div v-if="activities.length" class="activities flex-1 h-full mt-0.5">
      <div
        v-for="(activity, i) in localActivities"
        :key="activity.key"
        class="activity mt-2"
        tabindex="0"
      >
        <div
          class="w-full px-6 md:px-5 grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4"
        >
          <!-- Timeline icon column -->
          <div
            class="relative flex justify-center after:absolute after:left-[50%] after:top-3 after:-z-10 after:border-l after:border-outline-gray-modals"
            :class="[
              i != activities.length - 1 && 'after:h-full',
              !['email', 'feedback', 'call', 'comment', 'task'].includes(
                activity.type
              ) && 'after:top-6',
            ]"
          >
            <div
              class="z-1 flex items-center justify-center rounded-full bg-surface-white"
              :class="[
                ['email', 'feedback'].includes(activity.type)
                  ? 'my-1 h-9 w-9'
                  : 'h-6 w-6',
                !['email', 'feedback', 'call', 'comment', 'task'].includes(
                  activity.type
                ) && 'mt-[2px]',
              ]"
            >
              <Avatar
                v-if="activity.type === 'email' || activity.type === 'feedback'"
                size="lg"
                :label="activity.sender?.full_name"
                :image="getUser(activity.sender?.name).user_image"
                class="bg-surface-white absolute left-[0.7px]"
              />
              <CommentIcon
                v-else-if="activity.type === 'comment'"
                class="text-ink-gray-5 absolute left-[7.5px]"
              />
              <FeatherIcon
                v-else-if="activity.type === 'task'"
                name="check-square"
                class="text-gray-600 left-[7.5px] size-4"
              />
              <FeatherIcon
                v-else-if="activity.type === 'call'"
                :name="
                  activity.call_type === 'Incoming'
                    ? 'phone-incoming'
                    : 'phone-outgoing'
                "
                class="text-ink-gray-5 left-[7.5px] size-4"
              />
              <DotIcon
                v-else
                class="text-ink-gray-5 absolute left-[7.5px] top-[6px]"
              />
            </div>
          </div>
          <div
            class="mb-4 flex flex-1"
            :class="[
              i == activities.length - 1 && 'mb-5',
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
              class="py-2 px-3"
              @reply="(e) => emit('email:reply', e)"
            />
            <CommentBox
              v-else-if="activity.type === 'comment'"
              :activity="activity"
              @update="() => emit('update')"
            />

            <!-- TASK -->
            <Taskbox
              v-else-if="activity.type === 'task'"
              :activity="activity"
              @update="() => emit('update')"
            />

            <!-- CALL -->
            <HistoryBox
              v-else-if="activity.type === 'call'"
              :activity="activity"
            />

            <!-- FEEDBACK -->
            <FeedbackBox
              v-else-if="activity.type === 'feedback'"
              :activity="activity"
            />

            <!-- HISTORY -->
            <HistoryBox v-else :activity="activity" />
          </div>
        </div>
      </div>
    </div>
    <!-- Empty state -->
    <div
      v-else
      class="h-screen flex flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <component :is="emptyTextIcon" class="h-7.5 w-7.5" />
      <span class="text-lg font-medium text-ink-gray-8">
        {{ __(emptyText) }}
      </span>
    </div>
  </FadedScrollableDiv>
</template>

<script setup lang="ts">
import { computed, h, inject, nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Avatar, FeatherIcon } from "frappe-ui";
import { FadedScrollableDiv } from "@/components";
import {
  ActivityIcon,
  CommentIcon,
  DotIcon,
  EmailIcon,
  PhoneIcon,
} from "@/components/icons";
import LucideListTodo from "~icons/lucide/list-todo";
import { useUserStore } from "@/stores/user";
import { TicketActivity } from "@/types";
import { isElementInViewport } from "@/utils";
import { __ } from "@/translation";
import FeedbackBox from "../ticket-agent/FeedbackBox.vue";
import CommentBox from "@/components/CommentBox.vue";
import EmailArea from "@/components/EmailArea.vue";
import HistoryBox from "@/components/HistoryBox.vue";
import Taskbox from "@/components/view-controls/Taskbox.vue";
import TaskboxEditor from "@/components/view-controls/TaskboxEditor.vue";
import ActivityHeader from "@/components/ticket/ActivityHeader.vue";

const props = defineProps({
  activities: {
    type: Array as () => TicketActivity[],
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
const emit = defineEmits(["email:reply", "update", "new-email"]);
const route = useRoute();
const router = useRouter();
const { getUser } = useUserStore();
const ticketId = inject<string>("ticketId", "");
const showTaskEditor = ref(false);

watch(
  () => props.activities,
  async () => {
    await nextTick();
    setTimeout(() => {
      scrollToLatestActivity();
    }, 100);
  },
  { deep: true }
);
const localActivities = ref([...props.activities]);
watch(
  () => props.activities,
  (val) => {
    localActivities.value = [...val];
  },
  { immediate: true, deep: true }
);
function handleTaskCreated(task: any) {
  showTaskEditor.value = false;
  localActivities.value.push(task);
  emit("update");
}
const emptyText = computed(() => {
  if (props.title === __("Emails")) return "No email communications";
  if (props.title === __("Comments")) return "No comments found";
  if (props.title === __("Calls")) return "No calls made";
  if (props.title === __("Tasks")) return "No tasks found";
  return "No activity found";
});
const emptyTextIcon = computed(() => {

  let icon: any = ActivityIcon;
  if (props.title === __("Emails")) icon = EmailIcon;
  else if (props.title === __("Comments")) icon = CommentIcon;
  else if (props.title === __("Calls")) icon = PhoneIcon;
  else if (props.title === __("Tasks")) icon = LucideListTodo;
  return h(icon, { class: "text-gray-500" });
  let icon = ActivityIcon;
  if (props.title == "Emails") {
    icon = EmailIcon;
  } else if (props.title == "Comments") {
    icon = CommentIcon;
  } else if (props.title == "Calls") {
    icon = PhoneIcon;
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
  const elementId = hash.substring(1);
  nextTick(() => {
    setTimeout(() => {
      const element = document.getElementById(elementId);
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

watch(() => route.hash, scrollToLatestActivity);
watch(() => props.title, scrollToLatestActivity, { immediate: true });

defineExpose({ scrollToLatestActivity });
</script>

<style scoped>
.activity:focus {
  outline: none;
}
</style>
