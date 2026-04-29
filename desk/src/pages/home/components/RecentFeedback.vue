<template>
  <div class="w-full h-full overflow-hidden">
    <div class="flex flex-col rounded-md p-4 min-h-48 grow w-full h-full">
      <div class="flex flex-col sm:flex-row gap-4 h-full w-full">
        <div class="flex items-center justify-between sm:hidden">
          <div class="text-ink-gray-8 text-lg font-semibold">
            {{ __("Reviews") }}
          </div>
          <TabButtons
            :buttons="chartTabs"
            v-model="currentTab"
            class="sm:hidden"
          />
        </div>
        <!-- Left Panel: Summary Stats -->
        <div
          class="flex flex-col gap-4 min-w-72"
          :class="{ 'hidden sm:flex': currentTab === 'feedback' }"
        >
          <div class="items-center justify-between hidden sm:flex">
            <div class="text-ink-gray-8 text-lg font-semibold">
              {{ __("Reviews") }}
            </div>
            <TabButtons
              :buttons="chartTabs"
              v-model="currentTab"
              class="sm:hidden"
            />
          </div>
          <!-- Average Rating -->
          <div class="flex items-end justify-between gap-4">
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-1">
                <LucideStar class="size-4 fill-[#de9735] text-[#de9735]" />
                <div class="text-2xl font-medium text-ink-gray-8">
                  {{ chartConfig.averageRating }}
                </div>
              </div>
              <div
                class="flex items-center text-ink-gray-5 text-sm cursor-pointer hover:text-ink-gray-7"
                @click="redirectToSeeAllReviews"
              >
                {{ __("{0} reviews", chartConfig.totalFeedbacks) }}
                <FeatherIcon name="arrow-up-right" class="size-3.5 ml-0.5" />
              </div>
            </div>
            <div v-if="chartConfig.totalFeedbacks > 0" class="text-sm">
              {{ __("Your performance is") }}
              {{ performance }}!
            </div>
          </div>
          <!-- Bar Chart -->
          <div class="h-32 mt-2 w-full px-4">
            <ECharts
              v-if="chartConfig.totalFeedbacks > 0"
              :options="barChartOptions"
              class="w-full h-full"
            />
            <ECharts
              v-else
              :options="placeholderChartOptions"
              class="w-full h-full"
            />
          </div>
        </div>
        <div class="hidden sm:block h-full w-[1px] bg-surface-gray-2"></div>

        <!-- Right Panel: Feedback Card -->
        <div
          class="flex-1 flex flex-col min-w-0"
          :class="{ 'hidden sm:flex': currentTab === 'rating' }"
        >
          <!-- Filters -->
          <div class="flex items-center justify-between mb-3">
            <Dropdown :options="periodOptions">
              <template #default>
                <Button :label="currentPeriodLabel" icon-right="chevron-down" />
              </template>
              <template #item-label="{ item }">
                <div
                  class="data-[disabled]:cursor-not-allowed group flex w-full items-center rounded px-2 text-base focus:outline-none focus:bg-surface-gray-3 data-[highlighted]:bg-surface-gray-3 data-[state=open]:bg-surface-gray-3 whitespace-nowrap text-ink-gray-7 cursor-pointer justify-between"
                >
                  <span>
                    {{ item.label }}
                  </span>
                </div>
              </template>
              <template #item-suffix="{ item }">
                <FeatherIcon
                  v-if="item.label == __(periodLabels[currentPeriod])"
                  name="check"
                  class="size-4"
                />
              </template>
            </Dropdown>
            <Dropdown :options="sortOptions" placement="right">
              <template #default>
                <Button :label="currentSortLabel" icon-right="chevron-down" />
              </template>
              <template #item-label="{ item }">
                <div
                  class="data-[disabled]:cursor-not-allowed group flex w-full items-center rounded px-2 text-base focus:outline-none focus:bg-surface-gray-3 data-[highlighted]:bg-surface-gray-3 data-[state=open]:bg-surface-gray-3 whitespace-nowrap text-ink-gray-7 cursor-pointer justify-between"
                >
                  <span>
                    {{ item.label }}
                  </span>
                </div>
              </template>
              <template #item-suffix="{ item }">
                <FeatherIcon
                  v-if="item.label == __(sortLabels[currentSort])"
                  name="check"
                  class="size-4"
                />
              </template>
            </Dropdown>
          </div>

          <!-- Feedback Card -->
          <div
            v-if="currentFeedback && chartConfig.totalFeedbacks > 0"
            class="flex-1 flex flex-col rounded-lg mt-2"
          >
            <!-- Ticket Info -->
            <div class="flex items-center gap-1 text-base text-ink-gray-5">
              <div
                class="flex items-center gap-0.5 hover:text-ink-gray-7 cursor-pointer font-medium"
                @click="goToTicket(currentFeedback)"
              >
                <FeatherIcon name="arrow-up-right" class="size-4" />
                {{ currentFeedback.name }}
              </div>
              <span class="text-ink-gray-4">·</span>
              <span class="truncate text-ink-gray-7 font-medium">{{
                currentFeedback.subject
              }}</span>
            </div>
            <hr class="my-2" />
            <!-- Rating & Title -->
            <div class="flex items-center gap-2 mb-2">
              <div
                class="flex items-center gap-1 p-1 pl-0 rounded"
                :class="[getRatingColor(currentFeedback.star_rating).text]"
              >
                <LucideStar
                  class="size-3.5"
                  :class="getRatingColor(currentFeedback.star_rating).text"
                />
                <span
                  class="text-base font-medium text-ink-gray-7"
                  :class="getRatingColor(currentFeedback.star_rating).text"
                  >{{ currentFeedback.star_rating }}</span
                >
              </div>
              <span class="text-base text-ink-gray-7 font-medium">{{
                currentFeedback.feedback || __("Feedback")
              }}</span>
            </div>

            <!-- Feedback Text -->
            <div class="text-p-base text-ink-gray-7 mb-3 line-clamp-3">
              {{
                currentFeedback.feedback_extra || __("No additional comments")
              }}
            </div>

            <!-- Contact & Navigation -->
            <div class="flex items-center justify-between mt-auto">
              <div class="flex items-center gap-1">
                <Avatar
                  :image="currentFeedback.contact_image"
                  :label="
                    currentFeedback.contact_name || currentFeedback.contact
                  "
                  size="sm"
                />
                <span class="text-sm text-ink-gray-6">{{
                  currentFeedback.contact_name || currentFeedback.contact
                }}</span>
                <span class="text-sm text-ink-gray-4">·</span>
                <span class="text-sm text-ink-gray-5">{{
                  timeAgo(currentFeedback.modified)
                }}</span>
              </div>
              <div class="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  @click="prevFeedback"
                  :disabled="currentIndex === 0"
                >
                  <FeatherIcon name="chevron-left" class="size-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  @click="nextFeedback"
                  :disabled="currentIndex >= chartConfig.feedbacks.length - 1"
                >
                  <FeatherIcon name="chevron-right" class="size-4" />
                </Button>
              </div>
            </div>
          </div>
          <div
            v-else
            class="flex flex-col justify-center items-center text-center gap-2 h-full w-full"
          >
            <div class="flex flex-col gap-2 max-w-60">
              <div class="text-base font-medium text-ink-gray-7">
                {{ __("No feedback") }}
              </div>
              <div class="text-base text-ink-gray-6">
                {{ __("You haven't received any feedback yet") }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type PropType } from "vue";
import {
  Avatar,
  Button,
  createResource,
  Dropdown,
  FeatherIcon,
  TabButtons,
  ECharts,
} from "frappe-ui";
import LucideStar from "~icons/lucide/star";
import { useRouter } from "vue-router";
import { dayjsLocal } from "frappe-ui";
import { __ } from "@/translation";
import { timeAgo } from "@/utils";
import type { EChartsOption } from "echarts";
import { useView } from "@/composables/useView";
import { View } from "@/types";

const router = useRouter();
const chartTabs = [
  { label: "Rating", value: "rating" },
  { label: "Feedback", value: "feedback" },
];
const currentTab = ref("rating");
const { views } = useView("HD Ticket");

interface Feedback {
  name: string;
  subject: string;
  feedback_rating: number;
  star_rating: number;
  feedback: string;
  feedback_extra: string;
  contact: string;
  contact_name: string;
  contact_image: string;
  modified: string;
}

interface Data {
  recent_feedbacks: Feedback[];
  total_feedbacks: number;
  average_rating: number;
  rating_distribution: Record<number, number>;
}

const props = defineProps({
  data: {
    type: Object as PropType<Data>,
    required: true,
  },
});

const currentIndex = ref(0);
const currentPeriod = ref("all_time");
const currentSort = ref("positive_first");

const periodOptions = computed(() => [
  {
    label: __("All Time"),
    onClick: () => changePeriod("all_time"),
  },
  {
    label: __("Last Week"),
    onClick: () => changePeriod("last_week"),
  },
  {
    label: __("Last Month"),
    onClick: () => changePeriod("last_month"),
  },
  {
    label: __("Last 3 Months"),
    onClick: () => changePeriod("last_3_months"),
  },
]);

const sortOptions = computed(() => [
  {
    label: __("Positive first"),
    onClick: () => changeSort("positive_first"),
  },
  {
    label: __("Negative first"),
    onClick: () => changeSort("negative_first"),
  },
]);

const periodLabels: Record<string, string> = {
  all_time: __("All Time"),
  last_week: __("Last Week"),
  last_month: __("Last Month"),
  last_3_months: __("Last 3 Months"),
};

const currentPeriodLabel = computed(() => {
  return periodLabels[currentPeriod.value] || __("All Time");
});

const sortLabels: Record<string, string> = {
  negative_first: __("Negative first"),
  positive_first: __("Positive first"),
};

const currentSortLabel = computed(() => {
  return sortLabels[currentSort.value] || __("Positive first");
});

const changePeriod = (period: string) => {
  if (currentPeriod.value == period) return;
  currentPeriod.value = period;
  currentIndex.value = 0;
  getRecentFeedbackResource.fetch();
};

const changeSort = (sort: string) => {
  if (currentSort.value == sort) return;
  currentSort.value = sort;
  currentIndex.value = 0;
  getRecentFeedbackResource.fetch();
};

const chartConfig = computed(() => {
  const _data = getRecentFeedbackResource.data ?? props.data;
  const feedbacks = _data?.recent_feedbacks || [];
  const totalFeedbacks = _data?.total_feedbacks || 0;
  const averageRating = _data?.average_rating || 0;
  const ratingDistribution = _data?.rating_distribution || {
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
  };

  return {
    feedbacks,
    totalFeedbacks,
    averageRating,
    ratingDistribution,
  };
});

const performance = computed(() => {
  if (chartConfig.value.averageRating >= 4) {
    return __("excellent");
  } else if (chartConfig.value.averageRating >= 3) {
    return __("good");
  } else if (chartConfig.value.averageRating >= 2) {
    return __("average");
  } else {
    return __("poor");
  }
});

const currentFeedback = computed(() => {
  return chartConfig.value.feedbacks[currentIndex.value] || null;
});

const barChartOptions = computed<EChartsOption>(() => {
  const distribution = chartConfig.value.ratingDistribution;
  const values = [1, 2, 3, 4, 5].map((star) => distribution[star] || 0);
  const maxValue = Math.max(...values);

  const data = [1, 2, 3, 4, 5].map((star, index) => {
    const value = values[index];
    const isMax = value > 0 && value === maxValue;
    return {
      value,
      itemStyle: {
        color: isMax ? "#de9735" : "#d1d5db",
        borderRadius: [4, 4, 0, 0],
      },
      label: {
        show: isMax,
        position: "top" as const,
        formatter: value > 0 ? String(value) : "",
        color: "#6b7280",
        fontSize: 12,
      },
      emphasis: {
        label: {
          show: true,
        },
      },
    };
  });

  return {
    grid: {
      left: 4,
      right: 4,
      top: 16,
      bottom: 20,
      containLabel: false,
    },
    xAxis: {
      type: "category",
      data: ["1", "2", "3", "4", "5"],
      axisLine: { show: true, lineStyle: { color: "#ededed" } },
      axisTick: { show: false },
      axisLabel: {
        color: "#6b7280",
        fontSize: 12,
      },
    },
    yAxis: {
      type: "value",
      show: false,
    },
    series: [
      {
        type: "bar",
        data,
        barWidth: 24,
        label: {
          position: "top",
          color: "#6b7280",
          fontSize: 12,
          formatter: (params: any) => (params.value > 0 ? params.value : ""),
        },
        emphasis: {
          focus: "none",
        },
      },
    ],
    tooltip: { show: false },
  };
});

const placeholderChartOptions = computed<EChartsOption>(() => {
  const placeholderValues = Array.from(
    { length: 5 },
    () => Math.floor(Math.random() * 11) + 3
  );
  const data = placeholderValues.map((value) => ({
    value,
    itemStyle: {
      color: "#f1f1f1",
      borderRadius: [4, 4, 0, 0],
    },
  }));

  return {
    grid: {
      left: 4,
      right: 4,
      top: 16,
      bottom: 20,
      containLabel: false,
    },
    xAxis: {
      type: "category",
      data: ["1", "2", "3", "4", "5"],
      axisLine: { show: true, lineStyle: { color: "#e2e2e2" } },
      axisTick: { show: false },
      axisLabel: {
        color: "#e2e2e2",
        fontSize: 12,
      },
    },
    yAxis: {
      type: "value",
      show: false,
    },
    series: [
      {
        type: "bar",
        data,
        barWidth: 24,
        label: { show: false },
        emphasis: { disabled: true },
      },
    ],
    tooltip: { show: false },
    animation: false,
  };
});

const redirectToSeeAllReviews = () => {
  const viewName = "STD-VIEW-ALL-FEEDBACK";
  const view = views.data?.find((v: View) => v.name === viewName);

  const query: any = {
    view: view?.name,
  };

  if (currentPeriod.value !== "all_time") {
    let dateFilter = "";
    if (currentPeriod.value === "last_week") {
      dateFilter = dayjsLocal()
        .subtract(7, "day")
        .format("YYYY-MM-DD HH:mm:ss");
    } else if (currentPeriod.value === "last_month") {
      dateFilter = dayjsLocal()
        .subtract(30, "day")
        .format("YYYY-MM-DD HH:mm:ss");
    } else if (currentPeriod.value === "last_3_months") {
      dateFilter = dayjsLocal()
        .subtract(90, "day")
        .format("YYYY-MM-DD HH:mm:ss");
    }

    if (dateFilter) {
      query.filters = JSON.stringify({
        modified: [">", dateFilter],
      });
    }
  }

  const route = router.resolve({
    name: "TicketsAgent",
    query,
  });
  window.open(route.href, "_blank");
};

const getRatingColor = (rating: number) => {
  if (rating >= 4)
    return {
      text: "text-ink-green-3 fill-ink-green-3",
      bg: "bg-surface-green-2",
    };
  if (rating >= 3)
    return {
      text: "text-ink-yellow-3 fill-ink-yellow-3",
      bg: "bg-surface-yellow-2",
    };
  return {
    text: "text-ink-red-3 fill-ink-red-3",
    bg: "bg-surface-red-2",
  };
};

const getRecentFeedbackResource = createResource({
  url: "helpdesk.api.agent_home.agent_home.get_recent_feedback",
  makeParams: () => ({
    period: currentPeriod.value,
    sort_order: currentSort.value,
  }),
});

const goToTicket = (feedback: Feedback) => {
  const route = router.resolve({
    name: "TicketAgent",
    params: { ticketId: feedback.name },
  });
  window.open(route.href, "_blank");
};

const nextFeedback = () => {
  if (currentIndex.value < chartConfig.value.feedbacks.length - 1) {
    currentIndex.value++;
  }
};

const prevFeedback = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
  }
};

onMounted(() => {
  if (!props.data?.recent_feedbacks) {
    getRecentFeedbackResource.submit();
  }
});
</script>
