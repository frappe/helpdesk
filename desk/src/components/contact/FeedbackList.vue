<template>
  <div class="flex-1 min-w-0">
    <!-- Header: title + sort tabs -->
    <div class="flex items-center justify-between pb-4">
      <h4 class="font-semibold text-ink-gray-8">
        {{ __("User Reviews") }}
      </h4>
      <TabButtons
        v-model="activeSort"
        :buttons="sortOptions"
        @update:modelValue="onSortChange"
      />
    </div>

    <!-- List -->
    <div class="flex flex-col gap-2 max-h-[65vh] overflow-y-auto pr-1">
      <template v-for="ticket in feedbackListResource.data" :key="ticket.name">
        <div
          class="flex cursor-pointer flex-col gap-2 rounded-md border border-outline-gray-1 bg-surface-white p-2.5 hover:bg-surface-gray-1"
          @click="goToTicket(ticket.name)"
        >
          <!-- Rating badge + ticket name -->
          <div class="flex items-center gap-2">
            <span
              class="inline-flex shrink-0 items-center gap-1 rounded-sm px-1.5 py-1 text-sm"
              :class="ratingBadgeClass(ticket.feedback_rating)"
            >
              <LucideStar class="size-3 fill-current" />
              {{ formatRating(ticket.feedback_rating) }}
            </span>
            <p class="truncate text-sm">
              <span class="text-ink-gray-5"># {{ ticket.name }}</span>
              <span class="ml-1 font-medium text-ink-gray-7">{{
                ticket.subject
              }}</span>
            </p>
          </div>

          <!-- Feedback title + body -->
          <div class="flex flex-col gap-1.5">
            <p
              v-if="ticket.feedback"
              class="text-sm font-medium text-ink-gray-7"
            >
              {{ ticket.feedback }}
            </p>
            <p v-if="ticket.feedback_extra" class="text-p-base text-ink-gray-6">
              {{ ticket.feedback_extra }}
            </p>
          </div>
        </div>
      </template>

      <!-- Load More -->
      <div
        class="flex justify-center py-6"
        v-if="feedbackListResource.hasNextPage"
      >
        <Button
          :loading="feedbackListResource.loading"
          :label="__('Load More')"
          icon-left="refresh-cw"
          @click="feedbackListResource.next()"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useContactFeedback } from "@/composables/contact";
import { __ } from "@/translation";
import { TabButtons } from "frappe-ui";
import { ref } from "vue";
import { useRouter } from "vue-router";
import LucideStar from "~icons/lucide/star";

const props = defineProps<{
  name: string;
}>();

const { feedbackListResource, feedbackCount } = useContactFeedback(props.name);

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
  feedbackListResource.update({ orderBy: orderByMap[value] });
  feedbackListResource.reload();
}

function formatRating(rating: number | undefined | null): number {
  if (!rating) return 0;
  return Number(rating) * 5;
}

function ratingBadgeClass(rating: number | undefined | null): string {
  const stars = formatRating(rating);
  if (stars >= 4) return "bg-green-100 text-green-700";
  if (stars >= 2.5) return "bg-yellow-100 text-yellow-700";
  return "bg-red-100 text-red-700";
}
</script>
