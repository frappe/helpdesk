<template>
  <div class="rounded-md p-4 grow w-full h-full overflow-hidden">
    <div
      class="flex sm:flex-row flex-col gap-4 sm:items-center sm:justify-between"
    >
      <div class="text-lg font-semibold text-ink-gray-8">
        {{ __("Pending Tickets") }}
      </div>
      <div class="w-max">
        <TabButtons :buttons="chartTabs" v-model="currentTab" />
      </div>
    </div>
    <div class="mt-5 h-full overflow-auto hide-scrollbar -mx-2">
      <div class="min-w-[1050px]">
        <div class="grid grid-cols-10 gap-2 text-sm text-gray-600 py-2 px-3">
          <div class="col-span-1">{{ __("ID") }}</div>
          <div class="col-span-3">{{ __("Subject") }}</div>
          <div class="col-span-1">{{ __("Status") }}</div>
          <div class="col-span-1">{{ __("Priority") }}</div>
          <div class="col-span-2">{{ __("Team") }}</div>
          <div class="col-span-2">{{ __("Reason") }}</div>
        </div>
        <hr class="mx-2" />
        <div v-if="chartConfig?.tickets?.length > 0">
          <div
            v-for="(ticket, index) in chartConfig?.tickets"
            @click="goToTicket(ticket)"
          >
            <div
              class="grid grid-cols-10 gap-2 text-sm items-center py-3 px-3 cursor-pointer hover:bg-gray-50 rounded"
            >
              <div class="col-span-1 truncate">{{ ticket.name }}</div>
              <div class="col-span-3 truncate">{{ ticket.subject }}</div>
              <div class="col-span-1 truncate">{{ ticket.status }}</div>
              <div class="col-span-1">
                <Badge
                  :label="ticket.priority"
                  :theme="getPriorityBadgeColor(ticket.priority_integer_value)"
                />
              </div>
              <div class="col-span-2 truncate">
                {{ ticket.agent_group || __("Not Assigned") }}
              </div>
              <div class="col-span-2 truncate">
                <div
                  v-if="ticket.reason"
                  class="flex items-center gap-1 text-ink-gray-7"
                >
                  <TimerIcon
                    v-if="ticket.reason.type === 'upcoming_sla'"
                    class="size-4 flex-shrink-0"
                  />
                  <TicketPlusIcon
                    v-else-if="ticket.reason.type === 'new_tickets'"
                    class="size-4 flex-shrink-0"
                  />
                  <CalendarIcon
                    v-else-if="ticket.reason.type === 'pending'"
                    class="size-4 flex-shrink-0"
                  />
                  <span class="truncate">{{ ticket.reason.text }}</span>
                </div>
                <span v-else class="text-ink-gray-4">{{
                  __("No reason")
                }}</span>
              </div>
            </div>
            <hr class="mx-2" v-if="index < chartConfig?.tickets?.length - 1" />
          </div>
          <div
            v-if="chartConfig?.tickets?.length == 10"
            class="p-2 pt-3 flex items-center gap-1 text-base text-ink-gray-5 cursor-pointer hover:text-ink-gray-7 w-max select-none"
            @click="goToAllPendingTickets"
          >
            {{ __("See all {0} tickets", chartConfig?.totalPendingTickets) }}
            <FeatherIcon name="arrow-right" class="size-4" />
          </div>
        </div>
        <div v-else class="relative">
          <div v-for="i in 10" :key="i">
            <div class="grid grid-cols-10 gap-2 py-3 px-3">
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-3 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-2 h-4 bg-surface-gray-1" />
              <div class="col-span-2 h-4 bg-surface-gray-1" />
            </div>
            <hr class="mx-2" v-if="i < 10" />
          </div>
          <div
            class="absolute inset-0 flex flex-col items-center justify-center"
          >
            <div class="bg-surface-white space-y-1 w-64 p-3 rounded">
              <div class="text-ink-gray-7 font-medium text-center text-base">
                {{ __("No pending tickets") }}
              </div>
              <div class="text-ink-gray-6 text-center text-base">
                {{ __("All tickets are resolved or in progress") }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { Badge, createResource, FeatherIcon, TabButtons } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import TimerIcon from "~icons/lucide/timer";
import TicketPlusIcon from "~icons/lucide/ticket-plus";
import CalendarIcon from "~icons/lucide/calendar";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const router = useRouter();
const { userId } = storeToRefs(useAuthStore());
const currentTab = ref("all");
const chartTabs = [
  {
    label: "All",
    value: "all",
  },
  {
    label: "SLA Due",
    value: "upcoming_sla",
  },
  {
    label: "Recent",
    value: "new_tickets",
  },
  {
    label: "Pending",
    value: "pending",
  },
];

const chartConfig = computed(() => {
  const _data = getPendingTicketsResource.fetched
    ? getPendingTicketsResource.data
    : props.data;
  const maxPriority = _data.max_priority;
  const minPriority = _data.min_priority;
  const tickets = _data.tickets;
  const totalPendingTickets = _data.total_pending_tickets;

  return {
    tickets,
    maxPriority,
    minPriority,
    totalPendingTickets,
  };
});

const getPendingTicketsResource = createResource({
  url: "helpdesk.api.agent_dashboard.get_pending_tickets",
});

function getPriorityBadgeColor(integerValue: number) {
  const min = chartConfig.value.minPriority;
  const max = chartConfig.value.maxPriority;
  const range = max - min;
  if (range === 0) return "gray";
  const position = (integerValue - min) / range;
  if (position < 0.25) return "red";
  if (position < 0.5) return "orange";
  if (position < 0.75) return "green";
  return "gray";
}

const goToTicket = (ticket: any) => {
  router.push({
    name: "TicketAgent",
    params: { ticketId: ticket.name },
  });
};

const goToAllPendingTickets = () => {
  const filters = {
    status_category: "Open",
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

onMounted(() => {
  if (!Array.isArray(props.data.tickets)) {
    getPendingTicketsResource.fetch({ ticket_type: currentTab.value });
  }
});

// Watch for tab changes and fetch tickets
watch(currentTab, (newTab) => {
  getPendingTicketsResource.fetch({ ticket_type: newTab });
});
</script>
