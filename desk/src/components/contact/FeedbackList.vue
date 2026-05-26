<template>
  <div class="flex-1 min-w-0">
    <!-- Header: title + sort tabs -->
    <div class="flex items-center justify-between ml-6">
      <h4 class="font-semibold text-ink-gray-8">
        User reviews ({{ feedbackCount.data ?? 0 }})
      </h4>
      <TabButtons
        v-model="activeSort"
        :buttons="sortOptions"
        @update:modelValue="onSortChange"
      />
    </div>

    <!-- List -->
    <div>
      <template
        v-for="(ticket, i) in feedbackListResource.data"
        :key="ticket.name"
      >
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
            v-if="ticket.feedback"
            class="text-p-sm text-ink-gray-6 line-clamp-2"
          >
            {{ ticket.feedback }}
          </p>
          <!-- Extra feedback -->
          <p
            v-if="ticket.feedback_extra"
            class="text-p-sm text-ink-gray-6 line-clamp-2"
          >
            {{ ticket.feedback_extra }}
          </p>
        </div>
        <hr v-if="i !== feedbackListResource.data!.length - 1" class="mx-6" />
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
