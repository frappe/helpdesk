<template>
  <div class="flex flex-col flex-1 min-h-0">
    <template v-if="loading && !tickets.length">
      <div
        class="py-16 text-center text-sm text-ink-gray-4 flex items-center justify-center"
      >
        <LoadingIndicator :scale="10" />
      </div>
    </template>
    <div
      v-else-if="!tickets.length"
      class="flex flex-col items-center justify-center gap-3 py-16 text-center h-full flex-1"
    >
      <LucideTicket class="h-10 w-10 text-ink-gray-4" />
      <p class="text-lg-medium text-ink-gray-7">
        {{ __("No related tickets found") }}
      </p>
    </div>
    <div v-else class="pb-6">
      <template v-for="(ticket, i) in tickets" :key="ticket.name">
        <div
          class="grid items-center py-3 px-1 text-sm text-ink-gray-8 cursor-pointer hover:bg-surface-gray-1 rounded transition-colors"
          :style="gridTemplateStyle"
          @click="goToTicket(ticket.name)"
        >
          <div class="text-ink-gray-6 font-base">{{ ticket.name }}</div>
          <div class="truncate font-medium max-w-[90%]">
            {{ ticket.subject }}
          </div>
          <div class="flex items-center gap-1.5">
            <IndicatorIcon :class="getStatus(ticket.status)?.parsed_color" />
            <span>{{ ticket.status }}</span>
          </div>
          <div v-if="!isMobileView" class="flex items-center gap-1.5">
            <TicketPriority :priority="ticket.priority" />
          </div>
        </div>
        <hr class="mx-1" v-if="i !== tickets.length - 1" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import TicketPriority from "@/components/TicketPriority.vue";
import { IndicatorIcon } from "@/components/icons";
import { useScreenSize } from "@/composables/screen";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { LoadingIndicator } from "frappe-ui";
import { computed } from "vue";
import { useRouter } from "vue-router";
import LucideTicket from "~icons/lucide/ticket";

const props = defineProps<{
  tickets: Array<{
    name: string;
    subject: string;
    status: string;
    priority: string;
  }>;
  loading: boolean;
}>();

const router = useRouter();
const { isMobileView } = useScreenSize();
const { getStatus } = useTicketStatusStore();

const gridTemplateStyle = computed(() =>
  isMobileView.value
    ? "grid-template-columns: 5rem 1fr 7rem"
    : "grid-template-columns: 6rem 1fr 8rem 7rem"
);

function goToTicket(ticket: string) {
  const route = router.resolve({
    name: "TicketAgent",
    params: { ticketId: String(ticket) },
  });
  window.open(route.href, "_blank");
}
</script>
