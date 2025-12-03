<template>
  <div class="rounded-md p-4 grow w-full h-full overflow-hidden">
    <div class="text-lg font-semibold text-ink-gray-8">
      {{ __("Pending Tickets") }}
    </div>
    <div class="mt-5 h-full overflow-auto hide-scrollbar -mx-2">
      <div class="min-w-[1050px]">
        <div class="grid grid-cols-10 gap-2 text-sm text-gray-600 py-2 px-3">
          <div class="col-span-1">{{ __("ID") }}</div>
          <div class="col-span-3">{{ __("Subject") }}</div>
          <div class="col-span-1">{{ __("Status") }}</div>
          <div class="col-span-1">{{ __("Priority") }}</div>
          <div class="col-span-2">{{ __("Team") }}</div>
          <div class="col-span-2">{{ __("Last Replied") }}</div>
        </div>
        <hr class="mx-2" />
        <div v-if="tickets?.length > 0">
          <div v-for="(ticket, index) in tickets" @click="goToTicket(ticket)">
            <div
              class="grid grid-cols-10 gap-2 text-sm items-center py-3 px-3 cursor-pointer hover:bg-gray-50 rounded"
            >
              <div class="col-span-1 truncate">{{ ticket.name }}</div>
              <div class="col-span-3 truncate">{{ ticket.subject }}</div>
              <div class="col-span-1 truncate">{{ ticket.status }}</div>
              <div class="col-span-1">
                <Badge
                  :label="ticket.priority"
                  :theme="getPriorityBadgeColor(ticket.integer_value)"
                />
              </div>
              <div class="col-span-2 truncate">
                {{ ticket.agent_group || __("Not Assigned") }}
              </div>
              <div class="col-span-2 truncate">
                <span v-if="ticket.last_agent_reply" class="text-ink-gray-7">
                  {{ dayjs.tz(ticket.last_agent_reply).fromNow() }}
                </span>
                <span v-else class="text-ink-gray-4">{{
                  __("Not replied")
                }}</span>
              </div>
            </div>
            <hr class="mx-2" v-if="index !== tickets.length - 1" />
          </div>
        </div>
        <div v-else class="relative">
          <div v-for="i in 5" :key="i">
            <div class="grid grid-cols-10 gap-2 py-3 px-3">
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-3 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-2 h-4 bg-surface-gray-1" />
              <div class="col-span-2 h-4 bg-surface-gray-1" />
            </div>
            <hr class="mx-2" v-if="i < 5" />
          </div>
          <div
            class="absolute inset-0 flex flex-col items-center justify-center"
          >
            <div class="bg-surface-white space-y-1 w-64 p-3 rounded">
              <div class="text-ink-gray-7 font-medium text-center text-base">
                {{ __("No pending tickets") }}
              </div>
              <div class="text-ink-gray-6 text-center text-base">
                {{ __("All tickets are resolved or in progress.") }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import dayjs from "dayjs";
import { Badge, createResource } from "frappe-ui";
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const router = useRouter();

const tickets = computed(() => {
  return getPendingTicketsResource.fetched
    ? getPendingTicketsResource.data.tickets
    : props.data.tickets || [];
});

const minPriority = computed(() => {
  return getPendingTicketsResource.fetched
    ? getPendingTicketsResource.data.min_priority
    : props.data.min_priority;
});

const maxPriority = computed(() => {
  return getPendingTicketsResource.fetched
    ? getPendingTicketsResource.data.max_priority
    : props.data.max_priority;
});

const getPendingTicketsResource = createResource({
  url: "helpdesk.api.agent_dashboard.get_pending_tickets",
});

function getPriorityBadgeColor(integerValue) {
  const min = minPriority.value;
  const max = maxPriority.value;
  const range = max - min;
  if (range === 0) return "gray";
  const position = (integerValue - min) / range;
  if (position < 0.25) return "red";
  if (position < 0.5) return "orange";
  if (position < 0.75) return "green";
  return "gray";
}

function getTimeRemainingClass(resolutionBy: string) {
  const now = dayjs();
  const resolutionTime = dayjs(resolutionBy);
  const diffInMinutes = resolutionTime.diff(now, "minute");

  if (diffInMinutes < 60) {
    return "text-red-600";
  } else if (diffInMinutes < 120) {
    return "text-orange-600";
  }
}

const goToTicket = (ticket: any) => {
  router.push({
    name: "TicketAgent",
    params: { ticketId: ticket.name },
  });
};

onMounted(() => {
  if (!Array.isArray(props.data.tickets)) {
    getPendingTicketsResource.fetch();
  }
});
</script>
