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
          class="truncate text-base row"
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
      class="truncate text-base"
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
</script>

<style></style>
