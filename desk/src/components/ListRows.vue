<template>
  <div class="mx-3 h-full overflow-y-auto sm:mx-5" v-if="showGroupedRows">
    <div v-for="group in groupedRows" :key="group.group">
      <ListGroupHeader :group="group">
        <div
          class="my-2 flex items-center gap-2 text-base font-medium text-ink-gray-8 justify-between w-full mr-1"
        >
          <div class="flex items-center gap-2 w-full">
            <component v-if="group.icon" :is="group.icon" />
            <div
              v-if="group.group.label != ''"
              class="flex items-end gap-1 w-full"
            >
              <span>{{ group.group.label }}</span>
              <span class="text-xs text-ink-gray-5"
                >{{
                  group.rows.length +
                  " Article" +
                  (group.rows.length > 1 ? "s" : "")
                }}
              </span>
            </div>
          </div>
          <Dropdown :options="actions(group)" v-if="groupByActions.length > 0">
            <Button variant="ghost">
              <template #icon>
                <IconMoreHorizontal class="h-4 w-4" />
              </template>
            </Button>
          </Dropdown>
        </div>
      </ListGroupHeader>
      <ListGroupRows :group="group" id="list-rows" class="!mt-0">
        <ListRow
          v-for="row in group.rows"
          :key="row.name"
          v-slot="{ idx, column, item }"
          :row="row"
          :class="[
            'truncate text-base row transition-all duration-200',
            getRowClass(row)
          ]"
        >
          <slot v-bind="{ idx, column, item, row }" />
        </ListRow>
      </ListGroupRows>
    </div>
  </div>
  <ListRows class="mx-3 sm:mx-5" v-else id="list-rows">
    <ListRow
      v-for="row in groupedRows"
      :key="row.name"
      v-slot="{ idx, column, item }"
      :row="row"
      :class="[
        'truncate text-base transition-all duration-200',
        getRowClass(row)
      ]"
    >
      <slot v-bind="{ idx, column, item, row }" />
    </ListRow>
  </ListRows>
</template>

<script setup>
import {
  Button,
  Dropdown,
  ListGroupHeader,
  ListGroupRows,
  ListRow,
  ListRows,
} from "frappe-ui";
import { computed, ref, watch } from "vue";

import IconMoreHorizontal from "~icons/lucide/more-horizontal";
const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  groupByActions: {
    type: Array,
    default: () => [],
  },
});

const groupedRows = ref(props.rows);

const actions = (group) => {
  let _actions = props.groupByActions.map((action) => {
    return {
      ...action,
      onClick: () => action.onClick(group),
    };
  });
  if (group.group.label == "General") {
    _actions = _actions.filter((action) => action.label === "Add New Article");
  }
  return _actions;
};

watch(
  () => props.rows,
  (val) => (groupedRows.value = val)
);

let showGroupedRows = computed(() => {
  return props.rows.every(
    (row) => row.group && row.rows && Array.isArray(row.rows)
  );
});

// Get status category from ticket status
function getStatusCategory(row) {
  // Check if row has status_category field (from backend)
  if (row.status_category) {
    return row.status_category;
  }
  
  // Fallback: determine from status name
  const closedStatuses = ["Closed", "Resolved"];
  const pausedStatuses = ["Replied", "Pending", "On Hold", "Awaiting Response"];
  
  if (closedStatuses.includes(row.status)) {
    return "Resolved";
  } else if (pausedStatuses.some(s => row.status?.includes(s))) {
    return "Paused";
  }
  
  return "Open";
}

// Check if ticket is overdue
function isOverdue(row) {
  if (!row.resolution_by) return false;
  const now = new Date();
  const resolutionDate = new Date(row.resolution_by);
  return resolutionDate < now && getStatusCategory(row) !== "Resolved";
}

// Get conditional row classes based on ticket state
function getRowClass(row) {
  const statusCategory = getStatusCategory(row);
  const overdue = isOverdue(row);
  
  const classes = [];
  
  // Hover effect
  classes.push("hover:shadow-sm", "hover:bg-surface-gray-1");
  
  return classes.join(" ");
}
</script>

<style scoped>
/* Enhanced row styles */
:deep(.list-row) {
  transition: all 0.15s ease-in-out;
}

:deep(.list-row:hover) {
  transform: translateX(2px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* Smooth transitions for inline edits */
:deep(.inline-edit-wrapper) {
  transition: background-color 0.2s ease;
}

:deep(.inline-edit-wrapper:hover) {
  background-color: rgba(0, 0, 0, 0.02);
}
</style>
