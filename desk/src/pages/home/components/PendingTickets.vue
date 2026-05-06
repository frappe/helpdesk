<template>
  <div class="flex flex-col rounded-md p-4 grow w-full h-full overflow-hidden">
    <div class="flex gap-4 items-center justify-between">
      <div
        class="flex items-center gap-2 text-lg font-semibold text-ink-gray-8"
      >
        {{ currentTitle }}
        <Tooltip :text="tooltipText" placement="top">
          <FeatherIcon name="info" class="size-3" />
        </Tooltip>
      </div>
      <div class="w-max">
        <TabButtons :buttons="chartTabs" v-model="currentTab" />
      </div>
    </div>
    <div class="flex flex-col mt-5 grow overflow-auto hide-scrollbar">
      <table class="w-full table-auto">
        <thead v-if="chartConfig?.tickets?.length > 0">
          <tr class="text-sm text-gray-600">
            <th class="p-2 text-left font-normal whitespace-nowrap">
              {{ __("ID") }}
            </th>
            <th class="p-2 text-left font-normal w-full">
              {{ __("Subject") }}
            </th>
            <th class="p-2 text-left font-normal min-w-20 whitespace-nowrap">
              {{ __("Status") }}
            </th>
            <th class="p-2 text-left font-normal min-w-20 whitespace-nowrap">
              {{ __("Priority") }}
            </th>
            <th class="p-2 text-left font-normal min-w-32 whitespace-nowrap">
              {{ __("Team") }}
            </th>
            <th class="p-2 text-left font-normal min-w-40 whitespace-nowrap">
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
            <td class="p-2 py-3 w-full max-w-0 truncate">
              {{ ticket.subject }}
            </td>
            <td class="p-2 py-3 min-w-20 truncate">
              {{ ticket.status }}
            </td>
            <td class="p-2 py-3 min-w-20 truncate">
              <Badge
                :label="ticket.priority"
                :theme="getPriorityBadgeColor(ticket.priority_integer_value)"
              />
            </td>
            <td class="p-2 py-3 min-w-36 truncate">
              {{ ticket.agent_group || __("Not Assigned") }}
            </td>
            <td class="p-2 py-3 min-w-40">
              <div
                v-if="ticket.reason"
                class="flex items-center gap-1 text-ink-gray-7 truncate w-full"
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
                <span class="truncate pr-2">{{ ticket.reason.text }}</span>
              </div>
              <span
                v-else
                class="text-ink-gray-4 truncate inline-block w-full align-bottom"
                >{{ __("No reason") }}</span
              >
            </td>
          </tr>
        </tbody>
        <tbody class="relative" v-else>
          <tr
            v-for="i in 8"
            :key="i"
            :class="i > 1 ? 'border-t border-gray-200' : ''"
          >
            <td class="p-2 py-3 min-w-8">
              <div class="h-4 w-full rounded-sm bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3 w-full max-w-0">
              <div class="h-4 w-full rounded-sm bg-surface-gray-1 max-w-full" />
            </td>
            <td class="p-2 py-3 min-w-14">
              <div class="h-4 w-full rounded-sm bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3 min-w-21">
              <div class="h-4 w-full rounded-sm bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3 min-w-28">
              <div class="h-4 w-full rounded-sm bg-surface-gray-1" />
            </td>
            <td class="p-2 py-3 min-w-40">
              <div class="h-4 w-full rounded-sm bg-surface-gray-1" />
            </td>
          </tr>
          <EmptyState
            class="absolute inset-0 z-10"
            v-if="chartConfig?.tickets?.length === 0"
            :title="emptyState.title"
            :description="emptyState.description"
            variant="overlay"
            text="md"
          />
        </tbody>
      </table>
      <div
        class="flex justify-between items-center text-sm mt-auto text-ink-gray-5 pl-2 pb-2"
      >
        <div>
          <div
            v-if="chartConfig?.totalPendingTickets > 6"
            class="flex items-center gap-1 cursor-pointer hover:text-ink-gray-7 w-max select-none mt-3"
            @click="redirectToSeeAllTickets"
          >
            {{
              __("See all {0} tickets", chartConfig?.totalPendingTickets + "")
            }}
            <FeatherIcon name="arrow-right" class="size-4" />
          </div>
        </div>
        <div v-if="chartConfig?.tickets?.length > 0" class="mt-3 mb-0.5">
          {{
            __(
              "Showing {0} of {1} {2}",
              chartConfig?.tickets?.length + "",
              chartConfig?.totalPendingTickets + "",
              chartConfig?.tickets?.length > 1 ? __("tickets") : __("ticket")
            )
          }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useView } from "@/composables/useView";
import { __ } from "@/translation";
import { Badge, createResource, FeatherIcon, TabButtons } from "frappe-ui";
import { computed, onMounted, ref, watch, type PropType } from "vue";
import { useRouter } from "vue-router";
import TimerIcon from "~icons/lucide/timer";
import TicketPlusIcon from "~icons/lucide/ticket-plus";
import CalendarIcon from "~icons/lucide/calendar";
import { View } from "@/types";
import EmptyState from "@/components/EmptyState.vue";

interface TicketReason {
  type: string;
  text: string;
  seconds_until_due?: number;
}

interface PendingTicket {
  name: string | number;
  subject: string;
  status: string;
  priority: string;
  priority_integer_value: number;
  agent_group?: string;
  agreement_status?: string;
  creation: string;
  resolution_by?: string;
  response_by?: string;
  reason?: TicketReason;
}

interface PendingTicketsData {
  max_priority: number;
  min_priority: number;
  tickets: PendingTicket[];
  total_pending_tickets: number;
}

const props = defineProps({
  data: {
    type: Object as PropType<PendingTicketsData>,
    required: true,
  },
});

const router = useRouter();
const { views } = useView("HD Ticket");
const currentTab = ref("upcoming_sla");
const chartTabs = [
  {
    label: __("SLA"),
    value: "upcoming_sla",
  },
  {
    label: __("Pending"),
    value: "pending",
  },
  {
    label: __("Recent"),
    value: "new_tickets",
  },
];

const titles: Record<string, string> = {
  upcoming_sla: __("SLA Alerts"),
  new_tickets: __("Recent Tickets"),
  pending: __("Pending Tickets"),
};

const currentTitle = computed(() => {
  return titles[currentTab.value] || __("Pending Tickets");
});

const tooltipTexts: Record<string, string> = {
  upcoming_sla: __("Tickets approaching or breached SLA"),
  new_tickets: __("Tickets assigned to you in the last 7 days"),
  pending: __("Tickets that are awaiting your response"),
};
const tooltipText = computed(() => {
  return tooltipTexts[currentTab.value];
});

const emptyStateLabel: Record<string, { title: string; description: string }> =
  {
    upcoming_sla: {
      title: __("All SLAs on track"),
      description: __("Great! All your tickets are within SLA"),
    },
    new_tickets: {
      title: __("No recently assigned tickets"),
      description: __("No new tickets assigned to you in the last 7 days"),
    },
    pending: {
      title: __("No pending tickets"),
      description: __("All your assigned tickets have been responded to"),
    },
  };

const emptyState = computed(() => {
  return emptyStateLabel[currentTab.value];
});

const chartConfig = computed(() => {
  const _data: PendingTicketsData = getPendingTicketsResource.fetched
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

const goToTicket = (ticket: PendingTicket) => {
  router.push({
    name: "TicketAgent",
    params: { ticketId: String(ticket.name) },
  });
};

const redirectToSeeAllTickets = () => {
  const tabToViewMap: Record<string, string> = {
    pending: "STD-VIEW-PENDING-TICKETS",
    upcoming_sla: "STD-VIEW-SLA-ALERTS",
    new_tickets: "STD-VIEW-RECENTLY-ASSIGNED-TICKETS",
  };

  const viewName = tabToViewMap[currentTab.value];
  const view = views.data?.find((v: View) => v.name === viewName);

  const route = router.resolve({
    name: "TicketsAgent",
    query: {
      view: view?.name,
    },
  });
  window.open(route.href, "_blank");
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
