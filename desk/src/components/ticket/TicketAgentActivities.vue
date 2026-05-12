<template>
  <ActivityHeader
    :title="title"
    @new-task="
      () => {
        editingTask = null;
        showTaskModal = true;
      }
    "
  />

  <FadedScrollableDiv
    class="flex flex-col flex-1 overflow-y-auto"
    :mask-length="20"
  >
    <div v-if="activities.length" class="activities flex-1 h-full mt-0.5">
      <div
        v-for="(activity, i) in activities"
        :key="activity.key"
        class="activity mt-2"
        tabindex="0"
      >
        <div
          class="w-full px-6 md:px-5 grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4"
        >
          <div
            class="relative flex justify-center after:absolute after:left-[50%] after:top-3 after:-z-10 after:border-l after:border-gray-200"
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
                class="text-gray-600 absolute left-[7.5px]"
              />

              <FeatherIcon
                v-else-if="activity.type === 'call'"
                :name="
                  activity.call_type === 'Incoming'
                    ? 'phone-incoming'
                    : 'phone-outgoing'
                "
                class="text-gray-600 left-[7.5px] size-4"
              />

              <FeatherIcon
                v-else-if="activity.type === 'task'"
                name="check-square"
                class="text-gray-600 left-[7.5px] size-4"
              />

              <DotIcon
                v-else
                class="text-gray-600 absolute left-[7.5px] top-[6px]"
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
            <!-- EMAIL -->
            <EmailArea
              v-if="activity.type === 'email'"
              :activity="activity"
              :show-split-option="
                !activity.isFirstEmail && ticketStatus !== 'Closed'
              "
              class="py-2 px-3"
              @reply="(e) => emit('email:reply', e)"
            />

            <!-- COMMENT -->
            <CommentBox
              v-else-if="activity.type === 'comment'"
              :activity="activity"
              @update="() => emit('update')"
            />

            <!-- CALL -->
            <HistoryBox
              v-else-if="activity.type === 'call'"
              :activity="activity"
            />

            <!-- TASK -->
            <Taskbox
              v-else-if="activity.type === 'task'"
              :activity="activity"
              @edit="
                (task) => {
                  editingTask = task;
                  showTaskModal = true;
                }
              "
              @update="() => emit('update')"
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

    <!-- EMPTY STATE -->
    <div
      v-else
      class="h-screen flex flex-col items-center justify-center gap-3 text-xl font-medium text-gray-500"
    >
      <component :is="emptyTextIcon" class="h-7.5 w-7.5" />
      <span class="text-lg font-medium text-ink-gray-8">
        {{ __(emptyText) }}
      </span>
    </div>
  </FadedScrollableDiv>

  <!-- TASK MODAL -->
  <TaskModal
    v-model="showTaskModal"
    :ticketId="route.params.ticketId as string"
    :task="editingTask"
    @update="
      () => {
        editingTask = null;
        emit('update');
      }
    "
  />
</template>

<script setup lang="ts">
import { ref, computed, h, inject, nextTick, onMounted, watch } from "vue";

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

import FeedbackBox from "../ticket-agent/FeedbackBox.vue";
import CommentBox from "@/components/CommentBox.vue";
import EmailArea from "@/components/EmailArea.vue";
import HistoryBox from "@/components/HistoryBox.vue";
import Taskbox from "@/components/ticket/Taskbox.vue";
import ActivityHeader from "@/components/ticket/ActivityHeader.vue";
import TaskModal from "@/components/ticket/TaskModel.vue";

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

const emit = defineEmits(["email:reply", "update"]);

const route = useRoute();
const router = useRouter();

const { getUser } = useUserStore();

const communicationAreaRef: any = inject("communicationArea");
const makeCall = inject<() => void>("makeCall");

const showTaskModal = ref(false);
const editingTask = ref<object | null>(null);

const emptyText = computed(() => {
  if (props.title === "Emails") return "No email communications";
  if (props.title === "Comments") return "No comments found";
  if (props.title === "Calls") return "No calls made";
  if (props.title === "Tasks") return "No tasks found";
  return "No activity found";
});

const emptyTextIcon = computed(() => {
  let icon = ActivityIcon;
  if (props.title === "Emails") icon = EmailIcon;
  else if (props.title === "Comments") icon = CommentIcon;
  else if (props.title === "Calls") icon = PhoneIcon;
  else if (props.title === "Tasks") icon = LucideListTodo;
  return h(icon, { class: "text-gray-500" });
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
    const el = elements[elements.length - 1];
    if (el && !isElementInViewport(el)) {
      (el as any).scrollIntoViewIfNeeded();
      (el as HTMLElement).focus();
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

defineExpose({ scrollToLatestActivity });
</script>

<style scoped>
.activity:focus {
  outline: none;
}
</style>
