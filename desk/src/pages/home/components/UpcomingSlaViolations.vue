<template>
  <div class="rounded-md p-4 grow w-full h-full overflow-hidden">
    <div class="flex items-center justify-between">
      <div class="text-lg font-semibold text-ink-gray-8">
        {{ __("Upcoming SLA Violations") }}
      </div>
      <div class="flex items-center gap-2">
        <div class="flex items-center">
          <Button
            class="rounded-r-none border-r"
            @click="
              sortBy.direction = sortBy.direction == 'asc' ? 'desc' : 'asc'
            "
          >
            <AscendingIcon v-if="sortBy.direction == 'asc'" class="h-4" />
            <DescendingIcon v-else class="h-4" />
          </Button>
          <Dropdown :options="sortDropdownOptions">
            <template #default>
              <Button class="rounded-l-none">
                {{ sortBy.fieldname.label }}
              </Button>
            </template>
          </Dropdown>
        </div>
        <div
          v-if="priorityDropdownOptions.length < 7"
          class="flex items-center"
        >
          <Dropdown :options="priorityDropdownOptions">
            <template #default>
              <div class="flex items-center">
                <Button
                  :class="priorityFilter !== '' ? 'rounded-r-none' : ''"
                  :icon-right="priorityFilter !== '' ? '' : 'chevron-down'"
                >
                  {{ priorityFilter || __("Ticket priority") }}
                </Button>
              </div>
            </template>
          </Dropdown>
          <Button
            v-if="priorityFilter !== ''"
            class="rounded-l-none"
            icon="x"
            @click="priorityFilter = ''"
            :tooltip="__('Clear priority filter')"
          />
        </div>
        <Combobox
          v-else
          :options="getPriorityListResource?.data || []"
          v-model="priorityFilter"
          :placeholder="__('Ticket priority')"
        />
      </div>
    </div>
    <div class="mt-5 h-full overflow-auto hide-scrollbar -mx-2">
      <div class="min-w-[950px]">
        <div class="grid grid-cols-8 gap-2 text-sm text-gray-600 py-2 px-3">
          <div class="col-span-1">{{ __("ID") }}</div>
          <div class="col-span-2">{{ __("Subject") }}</div>
          <div class="col-span-1">{{ __("Status") }}</div>
          <div class="col-span-1">{{ __("Priority") }}</div>
          <div class="col-span-1">{{ __("Team") }}</div>
          <div class="col-span-1">{{ __("First Response") }}</div>
          <div class="col-span-1">{{ __("Resolution") }}</div>
        </div>
        <hr class="mx-2" />
        <div v-if="chartConfig?.tickets?.length > 0">
          <div
            v-for="(ticket, index) in chartConfig?.tickets"
            @click="goToTicket(ticket)"
          >
            <div
              class="grid grid-cols-8 gap-2 text-sm items-center py-3 px-3 cursor-pointer hover:bg-gray-50 rounded"
            >
              <div class="col-span-1 truncate">{{ ticket.name }}</div>
              <div class="col-span-2 truncate">{{ ticket.subject }}</div>
              <div class="col-span-1 truncate">{{ ticket.status }}</div>
              <div class="col-span-1">
                <Badge
                  :label="ticket.priority"
                  :theme="getPriorityBadgeColor(ticket.integer_value)"
                />
              </div>
              <div class="col-span-1">
                {{ ticket.agent_group || __("Not Assigned") }}
              </div>
              <div class="col-span-1 flex gap-1 items-center">
                <Badge
                  v-if="
                    ticket.first_responded_on &&
                    dayjs(ticket.first_responded_on).isBefore(
                      ticket.response_by
                    )
                  "
                  :label="__('Fulfilled')"
                  theme="green"
                  variant="outline"
                />
                <Badge
                  v-else-if="
                    dayjs(ticket.first_responded_on).isAfter(ticket.response_by)
                  "
                  :label="__('Failed')"
                  theme="red"
                  variant="outline"
                />
                <Tooltip v-else :text="dayjs(ticket.response_by).long()">
                  <div
                    class="flex items-center gap-1"
                    :class="getTimeRemainingClass(ticket.response_by)"
                  >
                    <TimerIcon class="size-4" />
                    <span class="text-p-sm">
                      {{ dayjs.tz(ticket.response_by).fromNow() }}
                    </span>
                  </div>
                </Tooltip>
              </div>
              <div class="col-span-1 flex gap-1 items-center">
                <Badge
                  v-if="getStatus(ticket.status)?.category === 'Paused'"
                  :label="__('Paused')"
                  theme="blue"
                  variant="outline"
                />
                <Badge
                  v-else-if="
                    ticket.resolution_date &&
                    dayjs(ticket.resolution_date).isBefore(ticket.resolution_by)
                  "
                  :label="__('Fulfilled')"
                  theme="green"
                  variant="outline"
                />
                <Badge
                  v-else-if="
                    dayjs(ticket.resolution_date || dayjs()).isAfter(
                      ticket.resolution_by
                    )
                  "
                  :label="__('Failed')"
                  theme="red"
                  variant="outline"
                />
                <Tooltip v-else :text="dayjs(ticket.resolution_by).long()">
                  <div
                    class="flex items-center gap-1"
                    :class="getTimeRemainingClass(ticket.resolution_by)"
                  >
                    <TimerIcon class="size-4" />
                    <span class="text-p-sm">
                      {{ dayjs.tz(ticket.resolution_by).fromNow() }}
                    </span>
                  </div>
                </Tooltip>
              </div>
            </div>
            <hr class="mx-2" />
          </div>
          <div
            v-if="chartConfig?.tickets?.length == 5"
            class="p-2 pt-3 flex items-center gap-1 text-base text-ink-gray-5 cursor-pointer hover:text-ink-gray-7 w-max select-none"
            @click="goToAllSlaViolations"
          >
            {{
              __("See all {0} tickets", chartConfig?.totalSlaViolationsCount)
            }}
            <FeatherIcon name="arrow-right" class="size-4" />
          </div>
        </div>
        <div v-else class="relative">
          <div v-for="i in 5" :key="i">
            <div class="grid grid-cols-8 gap-2 py-3 px-3">
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-2 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
              <div class="col-span-1 h-4 bg-surface-gray-1" />
            </div>
            <hr class="mx-2" v-if="i < 5" />
          </div>
          <div
            class="absolute inset-0 flex flex-col items-center justify-center"
          >
            <div class="bg-surface-white space-y-1 w-64 p-3 rounded">
              <div class="text-ink-gray-7 font-medium text-center text-base">
                {{ __("No upcoming SLA violations") }}
              </div>
              <div class="text-ink-gray-6 text-center text-base">
                {{ __("You’re well within your response windows") }}
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
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import dayjs from "dayjs";
import {
  Badge,
  Button,
  Combobox,
  createListResource,
  createResource,
  Dropdown,
  FeatherIcon,
  Tooltip,
} from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import TimerIcon from "~icons/lucide/timer";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const { getStatus } = useTicketStatusStore();
const router = useRouter();
const priorityFilter = ref("");
const sortBy = ref({
  direction: "asc",
  fieldname: {
    label: __("First Response"),
    value: "response_by",
  },
});
const { userId } = storeToRefs(useAuthStore());

const getPriorityListResource = createListResource({
  doctype: "HD Ticket Priority",
  fields: ["name"],
  auto: true,
  transform(data) {
    return data.map((d) => d.name);
  },
});

const chartConfig = computed(() => {
  const _data = upcomingSlaViolations.fetched
    ? upcomingSlaViolations.data
    : props.data;
  const totalSlaViolationsCount = _data?.total_sla_violations_count || 0;
  const tickets = _data?.upcoming_sla_violations || [];
  const minPriority = _data?.min_priority;
  const maxPriority = _data?.max_priority;

  return {
    totalSlaViolationsCount,
    tickets,
    minPriority,
    maxPriority,
  };
});

const priorityDropdownOptions = computed(() => {
  return (
    getPriorityListResource?.data?.map((priority: string) => ({
      label: priority,
      onClick: () => {
        priorityFilter.value = priority;
      },
    })) || []
  );
});

const sortDropdownOptions = computed(() => {
  return [
    {
      label: __("First Response"),
      onClick: () => {
        sortBy.value.fieldname = {
          label: __("First Response"),
          value: "response_by",
        };
      },
    },
    {
      label: __("Resolution"),
      onClick: () => {
        sortBy.value.fieldname = {
          label: __("Resolution"),
          value: "resolution_by",
        };
      },
    },
  ];
});

const upcomingSlaViolations = createResource({
  url: "helpdesk.api.agent_dashboard.get_upcoming_sla_violations",
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

const goToAllSlaViolations = () => {
  const filters: Record<string, any> = {
    sla: ["is", "set"],
    status_category: ["!=", "Closed"],
    agreement_status: ["in", ["First Response Due", "Resolution Due"]],
    _assign: ["LIKE", `%${userId.value}%`],
  };

  // Add priority filter if set
  if (priorityFilter.value) {
    filters.priority = priorityFilter.value;
  }

  router.push({
    name: "TicketsAgent",
    query: {
      filters: JSON.stringify(filters),
      order_by: `${sortBy.value.fieldname.value} ${sortBy.value.direction}`,
    },
  });
};

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

onMounted(() => {
  if (!props.data?.upcoming_sla_violations) {
    upcomingSlaViolations.submit();
  }
});

watch(
  [priorityFilter, sortBy],
  ([newPriority, newSortBy]) => {
    upcomingSlaViolations.submit({
      priority: newPriority,
      order_by: `${newSortBy.fieldname.value} ${newSortBy.direction}`,
    });
  },
  { deep: true }
);
</script>
