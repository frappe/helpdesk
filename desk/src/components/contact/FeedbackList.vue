<template>
  <div class="flex-1 min-w-0">
    <!-- Header: title + sort tabs -->
    <div class="flex items-center justify-between ml-6">
      <h4 class="font-semibold text-ink-gray-8">User reviews ({{ count }})</h4>
      <TabButtons
        v-model="activeSort"
        :buttons="sortOptions"
        @update:modelValue="onSortChange"
      />
    </div>

    <!-- Loading -->
    <template v-if="feedbackResource.loading && !feedbackResource.data?.length">
      <div class="flex items-center justify-center py-16">
        <LoadingIndicator :scale="10" />
      </div>
    </template>

    <!-- Empty -->
    <div
      v-else-if="!feedbackResource.data?.length"
      class="flex flex-col items-center justify-center gap-3 py-16 text-center"
    >
      <LucideStar class="h-10 w-10 text-ink-gray-4" />
      <p class="text-base font-medium text-ink-gray-7">No reviews yet</p>
    </div>

    <!-- List -->
    <div v-else>
      <template v-for="(ticket, i) in feedbackResource.data" :key="ticket.name">
        <div
          class="py-4 px-2 cursor-pointer hover:bg-surface-gray-1 rounded ml-4"
          @click="goToTicket(ticket.name)"
        >
          <!-- Rating badge -->
          <div class="flex items-center gap-1.5 mb-1.5">
            <span
              class="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-semibold"
              :class="ratingBadgeClass(ticket.feedback_rating)"
            >
              <LucideStar class="size-3 fill-current" />
              {{ formatRating(ticket.feedback_rating) }}
            </span>
          </div>

          <!-- Ticket name + subject -->
          <p class="text-sm mb-1">
            <span class="text-ink-gray-4"># {{ ticket.name }}</span>
            <span class="font-medium text-ink-gray-8 ml-1">{{
              ticket.subject
            }}</span>
          </p>

          <!-- Feedback text -->
          <p
            v-if="ticket.feedback_extra"
            class="text-p-sm text-ink-gray-6 line-clamp-2"
          >
            {{ ticket.feedback_extra }}
          </p>
        </div>
        <hr v-if="i !== feedbackResource.data!.length - 1" class="mx-6" />
      </template>

      <!-- Load More -->
      <div class="flex justify-center py-6" v-if="feedbackResource.hasNextPage">
        <Button
          :loading="feedbackResource.loading"
          :label="__('Load More')"
          icon-left="refresh-cw"
          @click="feedbackResource.next()"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import type { ListResource } from "@/types";
import type { HDTicket } from "@/types/doctypes";
import { LoadingIndicator, TabButtons } from "frappe-ui";
import { ref } from "vue";
import { useRouter } from "vue-router";
import LucideStar from "~icons/lucide/star";

const props = defineProps<{
  feedbackResource: ListResource<HDTicket>;
  count: number;
}>();

const router = useRouter();

function goToTicket(name: string) {
  const route = router.resolve({
    name: "TicketAgent",
    params: { ticketId: String(name) },
  });
  window.open(route.href, "_blank");
}

type SortValue = "all" | "latest" | "positive" | "negative";

const sortOptions: { label: string; value: SortValue }[] = [
  { label: __("All"), value: "all" },
  { label: __("Latest"), value: "latest" },
  { label: __("Positive"), value: "positive" },
  { label: __("Negative"), value: "negative" },
];

const activeSort = ref<SortValue>("all");

const orderByMap: Record<SortValue, string | undefined> = {
  all: undefined,
  latest: "modified desc",
  positive: "feedback_rating desc",
  negative: "feedback_rating asc",
};

function onSortChange(value: SortValue) {
  props.feedbackResource.update({ orderBy: orderByMap[value] });
  props.feedbackResource.reload();
}

function formatRating(rating: number | undefined | null): string {
  if (!rating) return "0.0";
  return Number(rating).toFixed(1);
}

function ratingBadgeClass(rating: number | undefined | null): string {
  const r = rating ?? 0;
  if (r >= 4) return "bg-green-100 text-green-700";
  if (r >= 2.5) return "bg-yellow-100 text-yellow-700";
  return "bg-red-100 text-red-700";
}
</script>
