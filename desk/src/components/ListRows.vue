<template>
  <div class="mx-3 mt-2 h-full overflow-y-auto sm:mx-5" v-if="showGroupedRows">
    <div v-for="group in reactiveRows" :key="group.group">
      <ListGroupHeader :group="group">
        <div
          class="my-2 flex items-center gap-2 text-base font-medium text-ink-gray-8 justify-between w-full"
        >
          <div class="flex items-center gap-2 w-full">
            <component v-if="group.icon" :is="group.icon" />
            <div v-if="group.group.label == ''" class="text-ink-gray-4">
              {{ "Empty" }}
              <span class="text-xs text-ink-gray-6"
                >{{ group.rows.length + " Articles" }}
              </span>
            </div>
            <div v-else class="flex items-center gap-1 w-full">
              <span>{{ group.group.label }}</span>
              <span class="text-xs text-ink-gray-6"
                >{{ group.rows.length + " Articles" }}
              </span>
            </div>
          </div>
          <Dropdown :options="options">
            <Button variant="ghost">
              <template #icon>
                <IconMoreHorizontal class="h-4 w-4" />
              </template>
            </Button>
          </Dropdown>
        </div>
      </ListGroupHeader>
      <ListGroupRows :group="group" id="list-rows">
        <ListRow
          v-for="row in group.rows"
          :key="row.name"
          v-slot="{ idx, column, item }"
          :row="row"
          class="truncate text-base"
        >
          <slot v-bind="{ idx, column, item, row }" />
        </ListRow>
      </ListGroupRows>
    </div>
  </div>
  <ListRows class="mx-3 sm:mx-5" v-else id="list-rows">
    <ListRow
      v-for="row in reactiveRows"
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
  ListRows,
  ListRow,
  ListGroupHeader,
  ListGroupRows,
  Dropdown,
  Button,
} from "frappe-ui";

import { ref, computed, watch, h } from "vue";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
});

const reactiveRows = ref(props.rows);

const options = [
  {
    label: "Edit Title",
    icon: "edit",
    onClick: () => {},
  },
  {
    group: "Danger",
    hideLabel: true,
    items: [
      {
        label: "Delete",
        component: h(Button, {
          label: "Delete",
          variant: "ghost",
          iconLeft: "trash-2",
          theme: "red",
          style: "width: 100%; justify-content: flex-start;",
          onClick: () => {},
        }),
      },
    ],
  },
];

watch(
  () => props.rows,
  (val) => (reactiveRows.value = val)
);

let showGroupedRows = computed(() => {
  return props.rows.every(
    (row) => row.group && row.rows && Array.isArray(row.rows)
  );
});
</script>
