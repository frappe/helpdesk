<template>
  <div v-if="title === __('Tasks')" class="flex items-center justify-between px-6 md:px-5 py-4 w-full">
    <h3 class="text-lg font-semibold text-ink-gray-9">
      {{ title }}
    </h3>
    <Button
      variant="solid"
      icon-left="plus"
      @click="showNewTaskModal = true"
    >
      {{ __("New Task") }}
    </Button>
  </div>
  
  <ActivityHeader v-else :title="title" />

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
    <div v-if="activities.length" class="activities flex-1 h-full mt-0.5">
      <div
        v-for="(activity, i) in activities"
        :key="activity.key"
        class="activity"
        tabindex="0"
        :id="activity.key"
      >
        <div
          v-if="activity.type === 'task'"
         class="w-full px-6 md:px-5"
        >
          <Taskbox
            :activity="activity"
            :reload-tasks="() => emit('update')"
            @update="() => emit('update')"
            class="w-full"
          />
        </div>

        <!-- Non-task: timeline layout -->
        <div
          v-else
          class="w-full px-6 md:px-5 grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4"
        >
          <div
            class="relative flex justify-center after:absolute after:start-[50%] after:top-3 after:-z-10 after:border-s after:border-outline-gray-modals"
            :class="[
              i != activities.length - 1 && 'after:h-full',
              !['email', 'feedback', 'call', 'comment'].includes(activity.type) && 'after:top-6',
            ]"
          >
            <div
              class="z-1 flex items-center justify-center rounded-full bg-surface-white"
              :class="[
                ['email', 'feedback'].includes(activity.type) ? 'my-1 h-9 w-9' : 'h-6 w-6',
                !['email', 'feedback', 'call', 'comment'].includes(activity.type) && 'mt-[2px]',
              ]"
            >
              <Avatar
                v-if="activity.type === 'email' || activity.type === 'feedback'"
                size="lg"
                :label="activity.sender?.full_name"
                :image="getUser(activity.sender?.name).user_image"
                class="bg-surface-white absolute start-[0.7px]"
              />
              <CommentIcon
                v-else-if="activity.type === 'comment'"
                class="text-ink-gray-5 absolute start-[7.5px]"
              />
              <FeatherIcon
                v-else-if="activity.type === 'call'"
               :name="activity.call_type === 'Incoming' ? 'phone-incoming' : 'phone-outgoing'"
               class="text-ink-gray-5 absolute start-[7.5px] size-4"
               />

              <DotIcon
                v-else
                class="text-ink-gray-5 absolute start-[7.5px] top-[6px]"
              />
            </div>
          </div>

          <div
            class="flex flex-1 mb-4"
            :class="[
              i == activities.length - 1 && 'mb-5',
              !['email', 'feedback', 'call', 'comment'].includes(activity.type) && 'mt-[2px]',
            ]"
          >
            <EmailArea
              v-if="activity.type === 'email'"
              :activity="activity"
              :show-split-option="!activity.isFirstEmail && ticketStatus !== 'Closed'"
              class="py-2 px-3 flex-1 w-full"
              @reply="(e) => emit('email:reply', e)"
            />
            <CommentBox
              v-else-if="activity.type === 'comment'"
              :activity="activity"
              class="flex-1 w-full"
              @update="() => emit('update')"
            />
            <CallArea
              v-else-if="activity.type === 'call'"
              :activity="activity"
              class="flex-1 w-full"
            />
            <FeedbackBox
              v-else-if="activity.type === 'feedback'"
              :activity="activity"
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

    <!-- Empty state -->
    <div
      v-else
      class="h-screen flex flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <component :is="emptyTextIcon" class="h-7.5 w-7.5" />
      <span class="text-lg font-medium text-ink-gray-8">{{ __(emptyText) }}</span>
    </div>
  </FadedScrollableDiv>
</template>

<script setup lang="ts">
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
import { Avatar, FeatherIcon, Button } from "frappe-ui";
import { PropType, computed, h, inject, nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { __ } from "@/translation";
import ActivityHeader from "@/components/ticket/ActivityHeader.vue";
import FeedbackBox from "../ticket-agent/FeedbackBox.vue";
import CommentBox from "@/components/CommentBox.vue";
import EmailArea from "@/components/EmailArea.vue";
import HistoryBox from "@/components/HistoryBox.vue";
import CallArea from "@/components/CallArea.vue";
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

const emit = defineEmits(["email:reply", "update"]);

const route = useRoute();
const router = useRouter();

const { getUser } = useUserStore();
const makeCall = inject<() => void>("makeCall");

const showNewTaskModal = ref(false);

const injectedTicketId = inject<string | number>("ticketId", "");
const resolvedTicketId = computed(() =>
  String(props.ticketId || injectedTicketId || "").trim()
);

const activities = computed(() => {
  if (props.title === __("Activity")) {
    return props.activities.filter((activity) => activity.type !== "task");
  }
  return props.activities;
});

const emptyText = computed(() => {
  if (props.title === __("Emails")) return "No email communications";
  if (props.title === __("Comments")) return "No comments found";
  if (props.title === __("Calls")) return "No calls made";
  if (props.title === __("Tasks")) return "No tasks found";
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
    let el: HTMLElement | null;
    let e = document.getElementsByClassName("activity");
    el = e[e.length - 1] as HTMLElement;
    if (el && !isElementInViewport(el)) {
      el.focus();
    }
  }, 200);
}

function scrollToHash() {
  const hash = route.hash;
  if (hash) {
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
</script>
<style scoped>
.activity:focus {
  outline: none;
}
</style>
