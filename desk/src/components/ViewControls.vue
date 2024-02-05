<template>
  <div class="flex items-center justify-between p-4">
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
        :filters="props.filter.filters"
        :filterable-fields="props.filter.filterableFields"
        @event:filter="emitToParent"
      />
    </div>
    <!-- <div class="flex-none pe-2">
            <p class="text-lg">Sort</p>
        </div>
        <div class="flex-none pe-2">
            <p class="text-lg">View Settings</p>
        </div> -->
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Filter } from "@/components";
import { Dropdown, FeatherIcon } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
let currentPreset = ref("All Tickets");

const props = defineProps({
  filter: {
    type: Object,
    required: true,
  },
});

const presetFilters = [
  {
    label: "All Tickets",
    onClick: (e) => {
      emitToParent({
        event: "clear",
      });
    },
  },
  {
    label: "My Open Tickets",
    onClick: (e) => {
      const preset = getPresetFilters("Open");
      emitToParent({
        event: "preset",
        data: preset,
      });
    },
  },
  {
    label: "My Replied Tickets",
    onClick: (e) => {
      const preset = getPresetFilters("Replied");
      emitToParent({
        event: "preset",
        data: preset,
      });
    },
  },
  {
    label: "My Resolved Tickets",
    onClick: (e) => {
      const preset = getPresetFilters("Resolved");
      emitToParent({
        event: "preset",
        data: preset,
      });
    },
  },
  {
    label: "My Closed Tickets",
    onClick: (e) => {
      const preset = getPresetFilters("Closed");
      emitToParent({
        event: "preset",
        data: preset,
      });
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

const emit = defineEmits(["event:filter"]);

function emitToParent(data) {
  if (data.event === "clear") {
    currentPreset.value = "All Tickets";
  } else {
    currentPreset.value = "Filtered Tickets";
  }
  emit("event:filter", data);
}
</script>
