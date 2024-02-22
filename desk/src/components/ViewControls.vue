<template>
  <div class="flex items-center justify-between px-5 pb-4 pt-3">
    <div class="flex-none">
      <Dropdown :options="presetFilters">
        <template #default="{ open }">
          <Button :label="currentPreset">
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
    </div>

    <div class="grow"></div>

    <div class="flex-none px-1">
      <Filter
        :filters="filter.filters"
        :filterable-fields="filter.filterableFields"
        @event:filter="(e) => emitToParent(e, 'event:filter')"
      />
    </div>
    <div class="pe-2 flex-none">
      <Sort
        :sortable-fields="sort.sortableFields"
        :sorts="sort.sorts"
        @event:sort="(e) => emitToParent(e, 'event:sort')"
      />
    </div>
    <div class="flex-none px-1">
      <ColumnSettings
        :fields="column.fields"
        :columns="column.columns"
        @event:column="(e) => emitToParent(e, 'event:column')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Filter, Sort, ColumnSettings } from "@/components";
import { Dropdown, FeatherIcon } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
let currentPreset = ref("All Tickets");

const props = defineProps({
  filter: {
    type: Object,
    required: true,
  },
  sort: {
    type: Object,
    required: true,
  },
  column: {
    type: Object,
    required: true,
  },
});

const presetFilters = [
  {
    label: "All Tickets",
    onClick: (e) => {
      emitToParent(
        {
          event: "clear",
        },
        "event:filter"
      );
    },
  },
  {
    label: "My Open Tickets",
    onClick: (e) => {
      const preset = getPresetFilters("Open");
      emitToParent(
        {
          event: "preset",
          data: preset,
        },
        "event:filter"
      );
    },
  },
  {
    label: "My Replied Tickets",
    onClick: (e) => {
      const preset = getPresetFilters("Replied");
      emitToParent(
        {
          event: "preset",
          data: preset,
        },
        "event:filter"
      );
    },
  },
  {
    label: "My Resolved Tickets",
    onClick: (e) => {
      const preset = getPresetFilters("Resolved");
      emitToParent(
        {
          event: "preset",
          data: preset,
        },
        "event:filter"
      );
    },
  },
  {
    label: "My Closed Tickets",
    onClick: (e) => {
      const preset = getPresetFilters("Closed");
      emitToParent(
        {
          event: "preset",
          data: preset,
        },
        "event:filter"
      );
    },
  },
];

function getPresetFilters(status) {
  return {
    filters: [
      {
        field: props.filter.filterableFields.find(
          (f) => f.fieldname === "status"
        ),
        operator: "is",
        value: status,
      },
      {
        field: props.filter.filterableFields.find(
          (f) => f.fieldname === "_assign"
        ),
        operator: "is",
        value: authStore.userId,
      },
    ],
    filtersToApply: {
      status: ["=", status],
      _assign: ["LIKE", `%${authStore.userId}%`],
    },
  };
}

const emit = defineEmits(["event:filter", "event:sort", "event:column"]);

function emitToParent(data, event) {
  if (event === "event:filter") {
    if (data.event === "clear") {
      currentPreset.value = "All Tickets";
    } else {
      currentPreset.value = "Filtered Tickets";
    }
  }
  emit(event, data);
}
</script>
