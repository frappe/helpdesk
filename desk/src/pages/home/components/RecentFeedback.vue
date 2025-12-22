<template>
  <div class="w-full h-full overflow-hidden">
    <div class="flex flex-col rounded-md p-4 min-h-48 grow w-full h-full">
      <div class="text-ink-gray-8 text-lg font-semibold">
        {{ __("Your rating") }}
      </div>
      <div
        v-if="chartConfig.averageRating == 0"
        class="flex flex-col justify-center items-center text-center gap-2 h-full w-full"
      >
        <div class="flex flex-col gap-2 max-w-60">
          <div class="text-base font-medium text-ink-gray-7">
            {{ __("No feedback") }}
          </div>
          <div class="text-base text-ink-gray-6">
            {{ __("You haven't received any feedback yet.") }}
          </div>
        </div>
      </div>
      <div v-else class="flex flex-col gap-2 h-full w-full mt-4">
        <div class="flex items-end justify-between w-full gap-2">
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-2">
              <div class="flex items-center gap-1">
                <LucideStar class="size-4 fill-[#de9735] text-[#de9735]" />
                <div class="text-2xl font-medium text-ink-gray-8">
                  {{ chartConfig.averageRating }}
                </div>
              </div>
              <Tooltip
                text="Average rating across all tickets"
                :hover-delay="0.25"
                :placement="'top'"
              >
                <FeatherIcon name="info" class="size-4" />
              </Tooltip>
            </div>
            <div class="text-base text-ink-gray-5">
              {{ __("{0} reviews", chartConfig.totalFeedbacks) }}
            </div>
          </div>
          <div class="text-sm">
            {{ __("Your performance is") }}
            <span :class="performance.color">{{ performance.text }}</span
            >!
          </div>
        </div>
        <div
          class="relative h-[200px] mt-10"
          @mouseenter="stopRotation"
          @mouseleave="startRotation"
          @keydown="handleKeydown"
          tabindex="0"
          role="region"
          :aria-label="__('Recent feedback carousel')"
        >
          <div class="relative h-full">
            <div
              v-for="(feedback, index) in chartConfig.feedbacks"
              :key="feedback.name || index"
              class="flex flex-col absolute inset-0 bg-surface-white border border-outline-gray-2 rounded-lg p-4 shadow-sm transition-all duration-500 ease-in-out"
              :style="getStyle(index)"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1 text-base font-medium">
                  <LucideStar class="size-4 fill-[#de9735] text-[#de9735]" />
                  {{ feedback.feedback_rating * 5 }}
                </div>
                <div
                  class="text-p-sm font-medium text-ink-gray-4 hover:text-ink-gray-5 cursor-pointer select-none"
                  @click="
                    router.push({
                      name: 'TicketAgent',
                      params: { ticketId: feedback.name },
                    })
                  "
                >
                  #{{ feedback.name }}
                </div>
              </div>
              <p
                class="text-p-base font-medium text-ink-gray-8 truncate mt-2.5"
              >
                {{ feedback.feedback }}
              </p>
              <div class="text-p-base text-ink-gray-7 line-clamp-3 mt-0.5">
                {{ feedback.feedback_extra }}
              </div>
              <div class="flex items-center gap-2 mt-auto">
                <Avatar size="md" :label="feedback.contact" />
                <div class="text-p-base font-medium text-ink-gray-8">
                  {{ feedback.contact }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { Avatar, createResource, FeatherIcon, Tooltip } from "frappe-ui";
import LucideStar from "~icons/lucide/star";
import { useRouter } from "vue-router";
import { __ } from "@/translation";

const router = useRouter();

interface Feedback {
  name: string;
  feedback_rating: number;
  total_feedbacks: number;
  feedback: string;
  feedback_extra: string;
  contact: string;
}

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const performance = computed(() => {
  if (chartConfig.value.averageRating >= 4) {
    return { text: __("excellent"), color: "text-green-600" };
  } else if (chartConfig.value.averageRating >= 3) {
    return { text: __("good"), color: "text-green-600" };
  } else if (chartConfig.value.averageRating >= 2) {
    return { text: __("average"), color: "text-yellow-600" };
  } else {
    return { text: __("poor"), color: "text-red-600" };
  }
});

const chartConfig = computed(() => {
  const _data = getRecentFeedbackResource.fetched
    ? getRecentFeedbackResource.data
    : props.data;
  const feedbacks = _data.recent_feedbacks;
  const totalFeedbacks = _data.total_feedbacks;
  const averageRating = _data.average_rating;

  return {
    feedbacks,
    totalFeedbacks,
    averageRating,
  };
});

const getRecentFeedbackResource = createResource({
  url: "helpdesk.api.agent_dashboard.get_recent_feedback",
  type: "GET",
});

const currentIndex = ref(0);
let interval: number | null = null;

const startRotation = () => {
  if (interval) clearInterval(interval);
  interval = setInterval(() => {
    currentIndex.value =
      (currentIndex.value + 1) % chartConfig.value.feedbacks.length;
  }, 5000);
};

const stopRotation = () => {
  if (interval) {
    clearInterval(interval);
    interval = null;
  }
};

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === "ArrowLeft") {
    currentIndex.value =
      (currentIndex.value - 1 + chartConfig.value.feedbacks.length) %
      chartConfig.value.feedbacks.length;
  } else if (e.key === "ArrowRight") {
    currentIndex.value =
      (currentIndex.value + 1) % chartConfig.value.feedbacks.length;
  }
};

const getStyle = (index: number) => {
  const len = chartConfig.value.feedbacks.length;
  if (len === 0) return { zIndex: 0, transform: "", opacity: 0 };
  const diff = (index - currentIndex.value + len) % len;
  const offset = 20;
  let y,
    scale,
    opacity = 1,
    zIndex;
  if (diff === 0) {
    y = 0;
    scale = 1;
    zIndex = 10;
  } else if (diff === 1) {
    y = -offset;
    scale = 0.95;
    zIndex = 9;
  } else if (diff === 2) {
    y = -2 * offset;
    scale = 0.9;
    zIndex = 8;
  } else {
    y = -3 * offset;
    scale = 0.8;
    opacity = 0;
    zIndex = 7;
  }
  return {
    zIndex,
    transform: `translate(0px, ${y}px) scale(${scale})`,
    opacity,
  };
};

onMounted(() => {
  if (chartConfig.value.feedbacks.length > 0) startRotation();
  if (!props.data?.recent_feedbacks) {
    getRecentFeedbackResource.submit();
  }
});

onUnmounted(() => {
  stopRotation();
});
</script>
