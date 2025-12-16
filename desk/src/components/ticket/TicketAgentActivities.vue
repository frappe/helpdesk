<template>
  <ActivityHeader :title="title" />
  <FadedScrollableDiv
    ref="scrollContainerRef"
    class="flex flex-col flex-1 overflow-y-auto pb-6"
    :mask-length="20"
  >
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
              class="z-1 flex h-7 w-7 items-center justify-center rounded-full bg-white"
              :class="[['email', 'feedback'].includes(activity.type) && 'mt-2']"
            >
              <Avatar
                v-if="activity.type === 'email' || activity.type === 'feedback'"
                size="lg"
                :label="activity.sender?.full_name"
                :image="getUser(activity.sender?.name).user_image"
                class="bg-white absolute left-[1px]"
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
                class="text-gray-600 absolute left-[7.5px] size-4"
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
            <CallArea
              v-else-if="activity.type === 'call'"
              :activity="activity"
            />
            <FeedbackBox
              :activity="activity"
              v-else-if="activity.type === 'feedback'"
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
        @click="communicationAreaRef?.toggleEmailBox() ?? toggleEmailBox()"
      />
      <Button
        v-else-if="title == 'Comments'"
        label="New Comment"
        @click="communicationAreaRef?.toggleCommentBox() ?? toggleCommentBox()"
      />
      <Button
        v-else-if="title == 'Calls'"
        label="Make a Call"
        @click="makeCall()"
      />
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
} from "@/components/icons";
import { toggleCommentBox, toggleEmailBox } from "@/pages/ticket/modalStates";
import { useUserStore } from "@/stores/user";
import { TicketActivity } from "@/types";
import { Avatar, FeatherIcon } from "frappe-ui";
import {
  PropType,
  Ref,
  computed,
  defineAsyncComponent,
  h,
  inject,
  nextTick,
  ref,
  watch,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import FeedbackBox from "../ticket-agent/FeedbackBox.vue";

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

const CommentBox = defineAsyncComponent(
  () => import("@/components/CommentBox.vue")
);
const EmailArea = defineAsyncComponent(
  () => import("@/components/EmailArea.vue")
);
const HistoryBox = defineAsyncComponent(
  () => import("@/components/HistoryBox.vue")
);

const route = useRoute();
const router = useRouter();

const { getUser } = useUserStore();
const communicationAreaRef: Ref = inject("communicationArea");
const makeCall = inject<() => void>("makeCall");
const scrollContainerRef = ref<{ scrollableDiv?: HTMLElement | Ref<HTMLElement | null> } | null>(null);

const emptyText = computed(() => {
  let text = "No Activities";
  if (props.title == "Emails") {
    text = "No Email Communications";
  } else if (props.title == "Comments") {
    text = "No Comments";
    return text;
  } else if (props.title == "Calls") {
    text = "No Calls";
    return text;
  }
});

const emptyTextIcon = computed(() => {
  let icon = ActivityIcon;
  if (props.title == "Emails") {
    icon = EmailIcon;
  } else if (props.title == "Comments") {
    icon = CommentIcon;
  } else if (props.title == "Calls") {
    icon = PhoneIcon;
  }
  return h(icon, { class: "text-gray-500" });
});

function scrollToLatestActivity(force = false) {
  if (route.hash && !force) {
    scrollToHash();
    return;
  }
  nextTick(() => {
    requestAnimationFrame(() => {
      const containerRef = scrollContainerRef.value?.scrollableDiv as
        | HTMLElement
        | Ref<HTMLElement | null>
        | undefined;
      const container =
        (containerRef as Ref<HTMLElement | null>)?.value ||
        (containerRef as HTMLElement);
      const items = document.getElementsByClassName("activity");
      const el = items[items.length - 1] as HTMLElement | undefined;
      if (!el || !container) return;

      const containerRect = container.getBoundingClientRect();
      const elRect = el.getBoundingClientRect();
      const elTop = elRect.top - containerRect.top + container.scrollTop;
      const elBottom = elTop + elRect.height;
      const viewTop = container.scrollTop;
      const viewBottom = viewTop + container.clientHeight;
      const margin = 48;
      const inView = elTop >= viewTop && elBottom <= viewBottom - margin;

      if (force) {
        const maxScroll = Math.max(container.scrollHeight - container.clientHeight, 0);
        container.scrollTo({ top: maxScroll, behavior: "smooth" });
        el.focus?.();
        return;
      }

      if (!inView) {
        const targetTop = Math.max(elTop - margin, 0);
        container.scrollTo({ top: targetTop, behavior: "smooth" });
        el.focus?.();
      }
    });
  });
}
function scrollToHash() {
  const hash = route.hash;
  if (hash) {
    // Remove the # symbol
    const elementId = hash.substring(1);

    nextTick(() => {
      // Wait for activities to be rendered
      setTimeout(() => {
        const element = document.getElementById(elementId);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "center" });

          // Add highlight effect using Tailwind class
          element.classList.add("bg-yellow-100");

          // Remove highlight after 2 seconds
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
    // Only scroll when tab changes, not on every update
    // This prevents unwanted scrolling when activities reload due to field updates
    if (props.activities.length > 0) {
      scrollToLatestActivity();
    }
  },
  { immediate: false }
);

defineExpose({
  scrollToLatestActivity,
});
</script>
