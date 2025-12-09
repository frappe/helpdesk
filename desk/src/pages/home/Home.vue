<template>
  <LayoutHeader>
    <template #left-header>
      <div class="text-lg font-medium text-gray-900">{{ __("Home") }}</div>
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Button
          v-if="layout.length > 0 && !editing"
          :label="__('Refresh')"
          variant="subtle"
          :icon-left="'refresh-ccw'"
          @click="agentDashboard.reload({ reset_layout: false })"
          :disabled="agentDashboard.loading"
        />
        <Button
          v-if="editing && isDashboardModified"
          :label="__('Reset')"
          variant="subtle"
          :icon-left="'rotate-cw'"
          @click="onReset"
        />
        <Button
          v-if="editing"
          :label="__('Save')"
          variant="subtle"
          :icon-left="'check'"
          @click="onSave"
          :disabled="!isDirty"
        />
        <Button
          v-if="layout.length > 0 && !editing"
          :label="__('Edit')"
          variant="subtle"
          :icon-left="'edit'"
          @click="onEdit"
          :disabled="agentDashboard.loading"
        />
        <Button
          v-if="editing"
          :label="__('Cancel')"
          variant="subtle"
          @click="onCancel"
        />
        <Dropdown
          v-if="chartsDropdown.length > 0"
          :options="chartsDropdown"
          placement="right"
        >
          <Button
            :label="__('New')"
            variant="solid"
            icon-left="plus"
            :disabled="agentDashboard.loading"
          />
        </Dropdown>
      </div>
    </template>
  </LayoutHeader>
  <div class="h-screen overflow-auto">
    <div
      class="flex flex-col p-1 pt-4 md:p-5 mx-auto max-w-6xl w-full grow relative"
    >
      <div class="grow">
        <div
          v-if="layout.length > 0"
          class="text-xl font-semibold text-ink-gray-8 pl-2"
        >
          {{ __("Hey") }}, {{ userName }}
        </div>
        <div
          v-if="layout.length === 0"
          class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
        >
          <div class="flex flex-col items-center justify-center gap-1">
            <FeatherIcon name="layout" class="size-12 text-ink-gray-8" />
            <div class="text-xl font-semibold text-ink-gray-8">
              {{ __("No charts added") }}
            </div>
            <div class="text-sm text-ink-gray-5">
              {{ __("Add charts to get started") }}
            </div>
          </div>
        </div>
        <div class="mt-5">
          <GridLayout
            v-if="layout.length > 0"
            class="h-fit w-full"
            :class="[editing ? 'mb-[20rem] !select-none' : '']"
            :cols="50"
            :rowHeight="14"
            :disabled="!editing"
            :modelValue="layout.map((item) => item.layout)"
            @update:modelValue="onLayoutUpdate"
          >
            <template #item="{ index }">
              <div
                class="group relative flex h-full w-full p-2 text-ink-gray-8"
              >
                <div
                  class="flex h-full w-full items-center justify-center"
                  :class="
                    editing
                      ? 'pointer-events-none  [&>div:first-child]:rounded [&>div:first-child]:group-hover:ring-2 [&>div:first-child]:group-hover:ring-outline-gray-2'
                      : ''
                  "
                >
                  <ChartItem :item="layout[index]" />
                </div>
                <div
                  v-if="editing"
                  class="flex absolute right-0 top-0 bg-surface-gray-6 rounded cursor-pointer opacity-0 group-hover:opacity-100"
                >
                  <div
                    class="rounded p-1 hover:bg-surface-gray-5"
                    @click="layout.splice(index, 1)"
                  >
                    <FeatherIcon name="trash-2" class="size-3 text-ink-white" />
                  </div>
                </div>
              </div>
            </template>
          </GridLayout>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader } from "@/components";
import { Button, createResource, Dropdown, GridLayout, toast } from "frappe-ui";
import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth";
import { computed, provide, ref } from "vue";
import ChartItem from "./components/ChartItem.vue";
import { __ } from "@/translation";

const { userName } = storeToRefs(useAuthStore());
const editing = ref(false);
const layout = ref([]);
const oldLayout = ref([]);

const isDirty = computed(() => {
  return JSON.stringify(layout.value) !== JSON.stringify(oldLayout.value);
});

const agentDashboard = createResource({
  url: "helpdesk.api.agent_dashboard.get_dashboard",
  auto: true,
  onSuccess(data) {
    layout.value = data.layout;
  },
});

const isDashboardModified = computed(() => {
  const _layout = layout.value.map((item) => {
    return {
      chart: item.chart,
      layout: item.layout,
    };
  });
  return JSON.stringify(_layout) !== agentDashboard.data.default_layout;
});

provide("agentDashboard", agentDashboard);
provide("dashboardData", layout);

const saveDashboard = createResource({
  url: "frappe.client.set_value",
  makeParams() {
    const layoutData = layout.value.map((item) => {
      return {
        chart: item.chart,
        layout: item.layout,
      };
    });
    return {
      doctype: "HD Field Layout",
      name: agentDashboard.data.dashboard_id,
      fieldname: "layout",
      value: JSON.stringify(layoutData),
    };
  },
  onSuccess() {
    toast.success(__("Dashboard saved"));
  },
});

const chartsDropdown = computed(() => {
  const _charts = [
    {
      label: __("My Tickets"),
      chart: "agent_tickets",
      onClick: () =>
        addChart("agent_tickets", {
          w: 17,
          h: 9,
          minW: 14,
          minH: 9,
          maxH: 9,
        }),
    },
    {
      label: __("Upcoming SLA Violations"),
      chart: "upcoming_sla_violations",
      onClick: () =>
        addChart("upcoming_sla_violations", {
          w: 50,
          h: 25,
          minW: 25,
          minH: 25,
          maxH: 25,
        }),
    },
    {
      label: __("Average Time Metrics"),
      chart: "avg_time_metrics",
      onClick: () =>
        addChart("avg_time_metrics", {
          w: 50,
          h: 24,
          minW: 18,
          minH: 24,
          maxH: 44,
        }),
    },
    {
      label: __("Avg. First Response Time"),
      chart: "avg_first_response_time",
      onClick: () =>
        addChart("avg_first_response_time", {
          w: 17,
          h: 9,
          minW: 14,
          minH: 9,
          maxH: 9,
        }),
    },
    {
      label: __("Avg. Resolution Time"),
      chart: "avg_resolution_time",
      onClick: () =>
        addChart("avg_resolution_time", {
          w: 17,
          h: 9,
          minW: 14,
          minH: 9,
          maxH: 9,
        }),
    },
    {
      label: __("Your rating"),
      chart: "recent_feedback",
      onClick: () =>
        addChart("recent_feedback", {
          w: 16,
          h: 27,
          minW: 16,
          minH: 27,
          maxW: 27,
          maxH: 27,
        }),
    },
    {
      label: __("Recently Assigned Tickets"),
      chart: "recently_assigned_tickets",
      onClick: () =>
        addChart("recently_assigned_tickets", {
          w: 17,
          h: 27,
          minW: 16,
          minH: 27,
          maxH: 27,
        }),
    },
    {
      label: __("Pending Tickets"),
      chart: "pending_tickets",
      onClick: () =>
        addChart("pending_tickets", {
          w: 50,
          h: 24,
          minW: 25,
          minH: 24,
          maxH: 24,
        }),
    },
  ].filter((chart) => {
    return !layout.value.some((item) => item.chart === chart.chart);
  });
  return _charts;
});

type ChartSize = {
  w: number;
  h: number;
  minW?: number;
  minH?: number;
  maxW?: number;
  maxH?: number;
};

const addChart = (chart: string, config: ChartSize) => {
  if (!editing.value) {
    onEdit();
  }
  layout.value.unshift({
    chart: chart,
    data: {},
    layout: {
      x: 0,
      y: 0,
      w: config.w,
      h: config.h,
      i: Math.random().toString(),
      minW: config.minW,
      minH: config.minH,
      maxW: config.maxW,
      maxH: config.maxH,
    },
  });
};

const onEdit = () => {
  oldLayout.value = JSON.parse(JSON.stringify(layout.value));
  editing.value = true;
};

const onSave = () => {
  saveDashboard.submit();
  editing.value = false;
};

const onCancel = () => {
  layout.value = oldLayout.value;
  editing.value = false;
};

const onReset = () => {
  agentDashboard.submit({
    reset_layout: true,
  });
};

const onLayoutUpdate = (newLayout: any) => {
  layout.value.forEach((item, idx) => {
    item.layout = newLayout[idx];
  });
};
</script>
