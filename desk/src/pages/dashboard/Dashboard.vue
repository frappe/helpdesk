<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Dashboard</div>
      </template>
      <template #right-header> </template>
    </LayoutHeader>

    <div class="p-5 w-full overflow-y-scroll">
      <div class="mb-4 flex items-center gap-4">
        <DateRangePicker
          v-model="selectedPeriod"
          variant="outline"
          placeholder="Period"
          :formatter="(date: string) => {
            const dateObj = new Date(date);
            return dateObj.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: dateObj.getFullYear() === new Date().getFullYear() ? undefined : 'numeric',
            });
          }"
        />
        <Autocomplete
          v-model="selectedAgent"
          :options="agentOptions"
          placeholder="Agent"
        >
          <template #target="{ togglePopover }">
            <TextInput
              readonly
              type="text"
              :value="selectedAgent ? selectedAgent.label : ''"
              placeholder="Agent"
              class="w-full"
              variant="outline"
              @focus="togglePopover()"
            >
              <template #prefix>
                <LucideUser v-if="!selectedAgent" class="size-4 text-ink-gray-5" />
                 <img
                    v-else-if="selectedAgent"
                    :src="selectedAgent.image"
                    class="size-4 rounded-full"
                  />
              </template>
          </TextInput>
          </template>
          <template #item-prefix="{ option }">
            <img :src="option.image" class="h-4 w-4 mr-2 rounded-full" />
          </template>
        </Autocomplete>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <NumberChart
          v-for="(config, index) in numberCards"
          :key="index"
          class="border rounded-md"
          :config="config"
        />
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <div class="border rounded-md min-h-80">
          <AxisChart :config="ticketTrendConfig" />
        </div>
        <div class="border rounded-md min-h-80">
          <AxisChart :config="feedbackTrendConfig" />
        </div>
        <div class="border rounded-md">
          <DonutChart :config="ticketsByTeam" />
        </div>
        <div class="border rounded-md">
          <DonutChart :config="ticketsByType" />
        </div>
        <div class="border rounded-md">
          <DonutChart :config="ticketsByPriority" />
        </div>
        <div class="border rounded-md">
          <DonutChart :config="ticketsByChannel" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AxisChart, DateRangePicker, DonutChart, NumberChart, usePageMeta } from "frappe-ui";
import { ref } from "vue";
import LucideUser from "~icons/lucide/user";

const selectedPeriod = ref('');
const selectedAgent = ref(null);

const agentOptions = [
  {
    label: 'John Doe',
    value: 'john-doe',
    image: 'https://randomuser.me/api/portraits/men/59.jpg',
  },
  {
    label: 'Jane Doe',
    value: 'jane-doe',
    image: 'https://randomuser.me/api/portraits/women/58.jpg',
  },
  {
    label: 'John Smith',
    value: 'john-smith',
    image: 'https://randomuser.me/api/portraits/men/59.jpg',
  },
  {
    label: 'Jane Smith',
    value: 'jane-smith',
    image: 'https://randomuser.me/api/portraits/women/59.jpg',
  },
  {
    label: 'John Wayne',
    value: 'john-wayne',
    image: 'https://randomuser.me/api/portraits/men/57.jpg',
  },
  {
    label: 'Jane Wayne',
    value: 'jane-wayne',
    image: 'https://randomuser.me/api/portraits/women/51.jpg',
  },
]

const numberCards = [
  {
    title: "Tickets",
    value: 452,
    delta: -2,
    deltaSuffix: "%",
    negativeIsBetter: true,
  },
  {
    title: "% Resolved",
    value: 92,
    suffix: "%",
    delta: -3,
    deltaSuffix: "%",
  },
  {
    title: "% SLA Fulfilled",
    value: 86,
    suffix: "%",
    delta: -2,
    deltaSuffix: "%",
  },
  {
    title: "Avg. Resolution Time",
    value: 4,
    suffix: " days",
    delta: -0.2,
    deltaSuffix: " days",
    negativeIsBetter: true,
  },
  {
    title: "Avg. Feedback Rating",
    value: 4.5,
    suffix: "/5",
    delta: 0.2,
    deltaSuffix: " stars",
  },
];

const colors = [
  '#318AD8',
	'#F683AE',
	'#48BB74',
	'#F56B6B',
	'#FACF7A',
	'#44427B',
	'#5FD8C4',
	'#F8814F',
	'#15CCEF',
	'#A6B1B9',
]

const ticketTrendConfig = {
  data: [
    { date: new Date("2024-05-01"), open: 6, closed: 122, sla_fulfilled: 78 },
    { date: new Date("2024-05-02"), open: 8, closed: 163, sla_fulfilled: 82 },
    { date: new Date("2024-05-03"), open: 3, closed: 119, sla_fulfilled: 85 },
    { date: new Date("2024-05-04"), open: 7, closed: 161, sla_fulfilled: 80 },
    { date: new Date("2024-05-05"), open: 2, closed: 138, sla_fulfilled: 90 },
    { date: new Date("2024-05-06"), open: 8, closed: 113, sla_fulfilled: 88 },
    { date: new Date("2024-05-07"), open: 3, closed: 107, sla_fulfilled: 92 },
    { date: new Date("2024-05-08"), open: 9, closed: 102, sla_fulfilled: 95 },
    { date: new Date("2024-05-09"), open: 5, closed: 96, sla_fulfilled: 89 },
    { date: new Date("2024-05-10"), open: 9, closed: 92, sla_fulfilled: 91 },
    { date: new Date("2024-05-11"), open: 6, closed: 88, sla_fulfilled: 87 },
    { date: new Date("2024-05-12"), open: 8, closed: 83, sla_fulfilled: 93 },
    { date: new Date("2024-05-13"), open: 7, closed: 77, sla_fulfilled: 94 },
    { date: new Date("2024-05-14"), open: 7, closed: 72, sla_fulfilled: 96 },
    { date: new Date("2024-05-15"), open: 12, closed: 67, sla_fulfilled: 97 },
    { date: new Date("2024-05-16"), open: 16, closed: 62, sla_fulfilled: 98 },
    { date: new Date("2024-05-17"), open: 24, closed: 56, sla_fulfilled: 78 },
  ],
  title: "Tickets Trend",
  subtitle: "Average tickets per day is around 124",
  colors: colors,
  xAxis: {
    key: "date",
    type: "time",
    title: "Date",
    timeGrain: "day",
  },
  yAxis: {
    title: "Tickets",
  },
  y2Axis: {
    title: "% SLA",
    yMin: 0,
    yMax: 100,
  },
  stacked: true,
  series: [
    { name: "closed", type: "bar" },
    { name: "open", type: "bar" },
    { name: "sla_fulfilled", type: "line", showDataPoints: true, axis: 'y2' },
  ],
}

const feedbackTrendConfig = {
  data: [
    { date: new Date("2024-05-01"), rating: 4.5, rated_tickets: 67 },
    { date: new Date("2024-05-02"), rating: 4.6, rated_tickets: 89 },
    { date: new Date("2024-05-03"), rating: 4.7, rated_tickets: 95 },
    { date: new Date("2024-05-04"), rating: 4.8, rated_tickets: 120 },
    { date: new Date("2024-05-05"), rating: 4.9, rated_tickets: 79 },
    { date: new Date("2024-05-06"), rating: 5.0, rated_tickets: 59 },
    { date: new Date("2024-05-07"), rating: 4.8, rated_tickets: 82 },
    { date: new Date("2024-05-08"), rating: 4.7, rated_tickets: 91 },
    { date: new Date("2024-05-09"), rating: 4.6, rated_tickets: 103 },
    { date: new Date("2024-05-10"), rating: 4.5, rated_tickets: 87 },
    { date: new Date("2024-05-11"), rating: 4.6, rated_tickets: 93 },
    { date: new Date("2024-05-12"), rating: 4.7, rated_tickets: 73 },
    { date: new Date("2024-05-13"), rating: 4.8, rated_tickets: 79 },
    { date: new Date("2024-05-14"), rating: 4.9, rated_tickets: 80 },
    { date: new Date("2024-05-15"), rating: 4.6, rated_tickets: 92 },
    { date: new Date("2024-05-16"), rating: 4.3, rated_tickets: 112 },
    { date: new Date("2024-05-17"), rating: 4.7, rated_tickets: 95 },
  ],
  title: "Feedback Trend",
  subtitle: "Average feedback rating per day is around 4.8",
  colors: colors,
  xAxis: {
    key: "date",
    type: "time",
    title: "Date",
    timeGrain: "day",
  },
  yAxis: {
    title: "Rated Tickets",
  },
  y2Axis: {
    title: "Rating",
    yMin: 0,
    yMax: 5,
  },
  series: [
    { name: "rated_tickets", type: "bar" },
    { name: "rating", type: "line", showDataPoints: true, axis: 'y2', color: colors[2] },
  ],
};

const ticketsByPriority = {
  data: [
    { priority: "High", count: 120 },
    { priority: "Medium", count: 200 },
    { priority: "Low", count: 80 },
  ],
  title: "Tickets by Priority",
  subtitle: "Total tickets by priority",
  colors: colors,
  categoryColumn: "priority",
  valueColumn: "count",
};

const ticketsByTeam = {
  data: [
    { team: "Support", count: 300 },
    { team: "Development", count: 150 },
    { team: "Sales", count: 50 },

  ],
  title: "Tickets by Team",
  subtitle: "Total tickets by team",
  colors: colors,
  categoryColumn: "team",
  valueColumn: "count",
};

const ticketsByType = {
  data: [
    { type: "Bug", count: 200 },
    { type: "Feature", count: 23 },
    { type: "Task", count: 83 },
  ],
  title: "Tickets by Type",
  subtitle: "Total tickets by type",
  colors: colors,
  categoryColumn: "type",
  valueColumn: "count",
};

const ticketsByChannel = {
  data: [
    { channel: "Email", count: 12 },
    { channel: "Portal", count: 223 },
  ],
  title: "Tickets by Channel",
  subtitle: "Total tickets by channel",
  colors: colors,
  categoryColumn: "channel",
  valueColumn: "count",
}

usePageMeta(() => {
  return {
    title: "Dashboard",
  };
});
</script>
