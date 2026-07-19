<template>
  <ActivityHeader :title="title" />
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
        :id="activity.key"
      >
        <!-- single activity -->
        <div
          class="w-full px-6 md:px-5 grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4"
        >
          <div
            class="relative flex justify-center after:absolute after:start-[50%] after:top-3 after:-z-10 after:border-s after:border-outline-elevation-2"
            :class="[
              i != activities.length - 1 && 'after:h-full',
              !['email', 'feedback', 'call', 'comment'].includes(
                activity.type
              ) && 'after:top-6',
            ]"
          >
            <div
              class="z-1 flex items-center justify-center rounded-full bg-surface-base"
              :class="[
                ['email', 'feedback'].includes(activity.type)
                  ? 'my-1 h-9 w-9'
                  : 'h-6 w-6',
                !['email', 'feedback', 'call', 'comment'].includes(
                  activity.type
                ) && 'mt-[2px]',
              ]"
            >
              <Avatar
                v-if="activity.type === 'email' || activity.type === 'feedback'"
                size="lg"
                :label="activity.sender?.full_name"
                :image="getUser(activity.sender?.name).user_image"
                class="bg-surface-base absolute start-[0.7px]"
              />
              <CommentIcon
                v-else-if="activity.type === 'comment'"
                class="text-ink-gray-5 absolute start-[7.5px]"
              />
              <FeatherIcon
                v-else-if="activity.type === 'call'"
                :name="
                  activity.call_type === 'Incoming'
                    ? 'phone-incoming'
                    : 'phone-outgoing'
                "
                class="text-ink-gray-5 start-[7.5px] size-4"
              />
              <DotIcon
                v-else
                class="text-ink-gray-5 absolute start-[7.5px] top-[6px]"
              />
            </div>
          </div>
          <div
            class="mb-4 flex flex-1"
            :class="[
              i == activities.length - 1 && 'mb-5',
              !['email', 'feedback', 'call', 'comment'].includes(
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
      class="h-screen flex flex-col items-center justify-center gap-3 text-2xl-medium text-ink-gray-4"
    >
      <component :is="emptyTextIcon" class="h-7.5 w-7.5" />
      <span class="text-lg-medium text-ink-gray-8">{{ __(emptyText) }}</span>
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
import { useUserStore } from "@/stores/user";
import { TicketActivity } from "@/types";
import { isElementInViewport } from "@/utils";
import { Avatar, FeatherIcon } from "frappe-ui";
import { PropType, computed, h, inject, nextTick, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import FeedbackBox from "../ticket-agent/FeedbackBox.vue";
import CommentBox from "@/components/CommentBox.vue";
import EmailArea from "@/components/EmailArea.vue";
import HistoryBox from "@/components/HistoryBox.vue";

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

const route = useRoute();
const router = useRouter();

const { getUser } = useUserStore();
const makeCall = inject<() => void>("makeCall");

const emptyText = computed(() => {
  if (props.title === "Emails") return "No email communications";
  if (props.title === "Comments") return "No comments found";
  if (props.title === "Calls") return "No calls made";

  return "No activity found";
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
  return h(icon, { class: "text-ink-gray-4" });
});

onMounted(() => {
  nextTick(() => {
    document.querySelector(".activity")?.focus();
  });
});

// The URL hash serves two unrelated purposes on ticket pages, and this
// component must tell them apart:
//
// 1. Active-tab state. useActiveTabManager persists the currently selected
//    tab in the hash (#activity, #email, #comment, ...) so that a reload or a
//    shared URL restores the same tab. On mobile every non-default tab is
//    stored this way; on desktop the same happens for tabs after the first.
//
// 2. Activity deep-links. Notifications and agent search navigate to a ticket
//    with a hash that names one specific activity to scroll to and highlight,
//    e.g. #comment-<name> or #communication-<name> (see Notifications.vue,
//    MobileNotifications.vue and SearchAgent.vue).
//
// Only case 2 is a scroll target for scrollToHash(). scrollToHash() finishes
// by *removing* the hash from the URL (the deep-link is one-shot), so if a
// case-1 hash ever fell through to it, the active-tab state would be wiped
// and useActiveTabManager would snap back to the default tab — on mobile that
// showed up as "I open Activity and seconds later I'm back on Details". It
// even found an element to scroll to, because the lucide icon sprite defines
// <symbol id="activity">. Deep-link ids are always prefixed (the element ids
// come from CommentBox and EmailArea), while tab hashes are bare tab names —
// so only hashes with a known deep-link prefix are treated as deep-links,
// and a new or renamed tab cannot re-introduce the bug.
const deepLinkPrefixes = ["comment-", "communication-"];

// Returns the id of the activity element the current hash deep-links to
// (case 2 above), or "" when there is no hash or it is only active-tab state
// (case 1). Callers can therefore use it both as "should I scroll to a
// specific activity?" and as the element id to scroll to.
function linkedActivityId() {
  const id = route.hash.substring(1);
  return id && deepLinkPrefixes.some((p) => id.startsWith(p)) ? id : "";
}

function scrollToLatestActivity() {
  if (linkedActivityId()) {
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
  const elementId = linkedActivityId();
  if (elementId) {
    nextTick(() => {
      // Wait for activities to be rendered
      setTimeout(() => {
        const element = document.getElementById(elementId);
        if (element) {
          (element as any).scrollIntoViewIfNeeded();

          // Add highlight effect using Tailwind class
          element.classList.add("bg-surface-yellow-2");

          // Remove highlight after 2 seconds
          setTimeout(() => {
            element.classList.remove("bg-surface-yellow-2");
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
<style scoped>
.activity:focus {
  outline: none;
}
</style>
