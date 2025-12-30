<template>
  <div class="w-full h-full overflow-hidden">
    <div class="rounded-md p-4 grow min-w-[252px] h-full">
      <div class="space-y-2">
        <div class="text-lg font-semibold text-ink-gray-8">
          {{ __("Recently Assigned Tickets") }}
        </div>
        <div
          v-if="chartConfig.ticketCount > 0"
          class="text-base text-ink-gray-6"
        >
          {{ __("You have") }}
          {{ chartConfig.ticketCount }} {{ __("new tickets this week") }}
        </div>
      </div>
      <div
        v-if="chartConfig.ticketCount == 0"
        class="flex flex-col justify-center items-center text-center gap-2 h-full w-full"
      >
        <div class="flex flex-col gap-2 max-w-60">
          <div class="text-base font-medium text-ink-gray-7">
            {{ __("No tickets assigned this week") }}
          </div>
          <div class="text-base text-ink-gray-6">
            {{ __("You haven't been assigned any new tickets this week") }}
          </div>
        </div>
      </div>
      <div v-else class="space-y-5 mt-7">
        <div
          v-for="ticket in chartConfig.tickets"
          class="flex justify-between items-center gap-2 rounded relative group/child my-2 cursor-pointer"
          @click="goToTicket(ticket)"
        >
          <div class="text-base space-y-1 grow truncate">
            <div class="font-medium text-base text-ink-gray-7 truncate">
              {{ ticket.subject }}
            </div>
            <div class="text-ink-gray-5 truncate">
              {{ dateFormat(ticket.creation, "MMM DD, YYYY") }} · #{{
                ticket.name
              }}
            </div>
          </div>
          <div>
            <FeatherIcon name="chevron-right" class="size-5" />
          </div>
          <div
            class="absolute -top-2 -left-2 -z-10 rounded group-hover/child:bg-surface-gray-2"
            :style="{
              width: 'calc(100% + 16px)',
              height: 'calc(100% + 16px)',
            }"
          />
        </div>
        <div
          v-if="chartConfig.tickets?.length == 5"
          class="p-0 flex items-center gap-1 text-base text-ink-gray-5 cursor-pointer hover:text-ink-gray-7 w-max select-none"
          @click="goToAllTickets"
        >
          {{ __("See all {0} tickets", chartConfig.ticketCount) }}
          <FeatherIcon name="arrow-right" class="size-4" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { dateFormat } from "@/utils";
import { createResource } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const { userId } = storeToRefs(useAuthStore());

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const chartConfig = computed(() => {
  const _data = getRecentlyAssignedTickets.fetched
    ? getRecentlyAssignedTickets.data
    : props.data;

  const tickets = _data?.tickets;
  const ticketCount = _data?.count;
  return {
    tickets,
    ticketCount,
  };
});

const goToTicket = (ticket: any) => {
  router.push({
    name: "TicketAgent",
    params: { ticketId: ticket.name },
  });
};

const goToAllTickets = () => {
  const filters = {
    _assign: ["LIKE", `%${userId.value}%`],
  };

  router.push({
    name: "TicketsAgent",
    query: {
      filters: JSON.stringify(filters),
      order_by: "modified desc",
    },
  });
};

const getRecentlyAssignedTickets = createResource({
  url: "helpdesk.api.agent_dashboard.get_recently_assigned_tickets",
  type: "GET",
});

onMounted(() => {
  if (!props.data?.tickets) {
    getRecentlyAssignedTickets.submit();
  }
});
</script>
