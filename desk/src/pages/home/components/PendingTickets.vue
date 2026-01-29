<template>
  <div class="flex flex-col rounded-md p-4 grow w-full h-full overflow-hidden">
    <div class="flex gap-4 items-center justify-between">
      <div class="text-lg font-semibold text-ink-gray-8">
        {{ __("Pending Tickets") }}
      </div>
      <div class="w-max">
        <TabButtons :buttons="chartTabs" v-model="currentTab" />
      </div>
    </div>
    <div class="flex flex-col mt-5 grow overflow-auto hide-scrollbar">
      <table class="w-full table-auto">
        <thead>
          <tr class="text-sm text-gray-600">
            <th class="p-2 text-left font-normal whitespace-nowrap">
              {{ __("ID") }}
            </th>
            <th class="p-2 text-left font-normal">{{ __("Subject") }}</th>
            <th class="p-2 text-left font-normal whitespace-nowrap">
              {{ __("Status") }}
            </th>
            <th class="p-2 text-left font-normal whitespace-nowrap">
              {{ __("Priority") }}
            </th>
            <th class="p-2 text-left font-normal whitespace-nowrap">
              {{ __("Team") }}
            </th>
            <th class="p-2 text-left font-normal whitespace-nowrap">
              {{ __("Reason") }}
            </th>
          </tr>
        </thead>
        <tbody v-if="chartConfig?.tickets?.length > 0" class="grow">
          <tr
            v-for="ticket in chartConfig?.tickets"
            :key="ticket.name"
            @click="goToTicket(ticket)"
            class="text-sm cursor-pointer hover:bg-gray-50 border-t border-gray-200"
          >
            <td class="p-2 py-3 whitespace-nowrap">{{ ticket.name }}</td>
            <td class="p-2 py-3 max-w-xs truncate">{{ ticket.subject }}</td>
            <td class="p-2 py-3 whitespace-nowrap">{{ ticket.status }}</td>
            <td class="p-2 py-3 whitespace-nowrap">
              <Badge
                :label="ticket.priority"
                :theme="getPriorityBadgeColor(ticket.priority_integer_value)"
              />
            </td>
            <td class="p-2 py-3 whitespace-nowrap">
              {{ ticket.agent_group || __("Not Assigned") }}
            </td>
            <td class="p-2 py-3 whitespace-nowrap">
              <div
                v-if="ticket.reason"
                class="flex items-center gap-1 text-ink-gray-7"
                :class="getReasonColorClass(ticket.reason)"
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
                <span>{{ ticket.reason.text }}</span>
              </div>
              <span v-else class="text-ink-gray-4">{{ __("No reason") }}</span>
            </td>
          </tr>
          <tr
            v-for="i in Math.max(0, 6 - chartConfig?.tickets?.length)"
            :key="'placeholder-' + i"
            class="border-t border-gray-100"
          >
            <td v-for="j in 6" :key="j" class="p-2 py-3">
              <div class="h-5 w-full bg-surface-gray-1" />
            </td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr v-for="i in 10" :key="i" class="border-t border-gray-200">
            <td class="p-2 py-3">
              <div class="h-4 w-16 bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3">
              <div class="h-4 w-48 bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3">
              <div class="h-4 w-16 bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3">
              <div class="h-4 w-16 bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3">
              <div class="h-4 w-24 bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3">
              <div class="h-4 w-32 bg-surface-gray-1" />
            </td>
          </tr>
        </tbody>
      </table>
      <div
        v-if="chartConfig?.tickets?.length === 0"
        class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
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
      <div
        v-if="chartConfig?.totalPendingTickets > 6"
        class="p-2 flex items-center gap-1 text-base text-ink-gray-5 cursor-pointer hover:text-ink-gray-7 w-max select-none"
        @click="redirectToSeeAllTickets"
      >
        {{ __("See all {0} tickets", chartConfig?.totalPendingTickets) }}
        <FeatherIcon name="arrow-right" class="size-4" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useView } from "@/composables/useView";
import { Badge, createResource, FeatherIcon, TabButtons } from "frappe-ui";
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
const { views } = useView("HD Ticket");
const currentTab = ref("upcoming_sla");
const chartTabs = [
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
  url: "helpdesk.api.agent_home.agent_home.get_pending_tickets",
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

function getReasonColorClass(reason: {
  text: string;
  seconds_until_due?: number;
}) {
  if (reason.text.includes("overdue")) {
    return "text-red-500";
  }

  if (
    reason.seconds_until_due !== undefined &&
    reason.seconds_until_due !== null
  ) {
    const oneHour = 3600;
    const twoHours = 7200;
    if (reason.seconds_until_due <= oneHour) {
      return "text-red-500";
    }
    if (reason.seconds_until_due <= twoHours) {
      return "text-orange-500";
    }
  }
  return "";
}

const goToTicket = (ticket: any) => {
  router.push({
    name: "TicketAgent",
    params: { ticketId: ticket.name },
  });
};

const redirectToSeeAllTickets = () => {
  const tabToViewMap: Record<string, string> = {
    pending: "Pending tickets",
    upcoming_sla: "SLA due",
    new_tickets: "Recently assigned tickets",
  };

  const viewLabel = tabToViewMap[currentTab.value];
  const view = views.data?.find((v: any) => v.label === viewLabel);

  router.push({
    name: "TicketsAgent",
    query: {
      view: view.name,
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
