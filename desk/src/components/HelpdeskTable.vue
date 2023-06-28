<template>
  <div class="w-full overflow-hidden overflow-x-auto">
    <div
      v-if="isEmpty(data)"
      class="flex h-full w-full items-center justify-center text-base text-gray-700"
    >
      {{ emptyMessage }}
    </div>
    <div
      v-else
      class="flex h-full w-max min-w-full flex-col overflow-y-hidden text-gray-700"
    >
      <div
        class="border-y border-gray-200 bg-white px-6 py-1.5 text-sm text-gray-600"
      >
        <div class="flex w-full items-center gap-2 px-3">
          <Input
            v-if="!hideCheckbox"
            type="checkbox"
            input-class="cursor-pointer text-gray-900"
            class="mr-1"
            :value="allSelected"
            @click="toggleAllRows"
          />
          <div
            v-for="column in columns"
            :key="column.title"
            :class="isColVisible(column) ? column.colClass : ''"
          >
            <div v-if="isColVisible(column)">
              {{ column.title }}
            </div>
          </div>
          <div v-if="!hideColumnSelector" class="ml-auto">
            <Popover>
              <template #target="{ togglePopover }">
                <IconAdd
                  class="h-4 w-4 cursor-pointer"
                  @click="togglePopover"
                />
              </template>
              <template #body-main>
                <div
                  class="flex w-48 flex-col gap-2 p-3 text-base text-gray-800"
                >
                  <div
                    v-for="column in columns.filter((c) => c.isTogglable)"
                    :key="column.colKey"
                    class="flex items-center justify-between"
                  >
                    {{ column.title }}
                    <Switch
                      v-model="togglableColumns[column.colKey]"
                      size="md"
                    />
                  </div>
                </div>
              </template>
            </Popover>
          </div>
        </div>
      </div>
      <div class="divide-y overflow-y-auto px-6 text-base">
        <div
          v-for="row in data"
          :key="row[rowKey]"
          class="group flex h-11 w-full items-center gap-2 px-3 py-2 transition"
          :class="{
            'bg-gray-200': selection.has(row[rowKey]),
            'hover:bg-gray-300': selection.has(row[rowKey]),
            'hover:bg-gray-100': !selection.has(row[rowKey]),
            'cursor-pointer': emitRowClick,
          }"
          @click="onRowClick(row)"
        >
          <Input
            v-if="!hideCheckbox"
            type="checkbox"
            input-class="cursor-pointer text-gray-900"
            class="mr-1"
            :value="selection.has(row[rowKey])"
            @click="toggleRow(row[rowKey])"
          />
          <div
            v-for="column in columns"
            :key="column.colKey"
            :class="isColVisible(column) ? column.colClass : ''"
          >
            <slot v-if="isColVisible(column)" :name="column.colKey" :data="row">
              <div class="line-clamp-1">
                {{ row[column.colKey] || "—" }}
              </div>
            </slot>
          </div>
          <div v-if="slots['row-extra']" class="ml-auto">
            <slot name="row-extra" :data="row" />
          </div>
        </div>
      </div>
    </div>
    <transition
      enter-active-class="duration-300 ease-out"
      enter-from-class="transform opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="transform opacity-0"
    >
      <div
        v-if="selection.size"
        class="fixed inset-x-0 bottom-5 mx-auto w-max text-base"
      >
        <div
          class="selection-bar flex items-center gap-4 rounded-lg bg-white px-4 py-2"
        >
          <div class="w-64">
            <div class="inline-block align-middle">
              <Input
                type="checkbox"
                :value="true"
                :disabled="true"
                input-class="text-gray-900"
              />
            </div>
            <div class="inline-block pl-2 align-middle text-gray-900">
              <slot name="actions-text">
                {{ selectionText }}
              </slot>
            </div>
          </div>
          <slot name="actions" :selection="selection" />
          <div class="text-gray-300">&#x007C;</div>
          <Button
            class="text-gray-700"
            :disabled="allSelected"
            variant="ghost"
            @click="toggleAllRows(true)"
          >
            Select all
          </Button>
          <FeatherIcon
            name="x"
            class="h-4 w-4 cursor-pointer text-gray-600"
            @click="toggleAllRows(false)"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, toRefs, useSlots } from "vue";
import { FeatherIcon, Popover, Switch } from "frappe-ui";
import { isEmpty } from "lodash";
import IconAdd from "~icons/espresso/add";

type Column = {
  title: string;
  colKey: string;
  colClass?: string;
  isTogglable?: boolean;
};
type RowKey = string;
type SelectionKey = string | number;

const props = defineProps({
  columns: {
    type: Array<Column>,
    required: true,
  },
  data: {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    type: Array<Record<any, any>>,
    required: true,
  },
  rowKey: {
    type: String,
    required: true,
  },
  selection: {
    type: Set<SelectionKey>,
    required: false,
    default: () => new Set(),
  },
  emitRowClick: {
    type: Boolean,
    required: false,
    default: false,
  },
  hideCheckbox: {
    type: Boolean,
    required: false,
    default: false,
  },
  hideColumnSelector: {
    type: Boolean,
    required: false,
    default: false,
  },
  emptyMessage: {
    type: String,
    required: false,
    default: "🙇 Such empty",
  },
});

const emit = defineEmits<{
  (event: "row-click", key: SelectionKey): void;
  (event: "update:selection", selection: Set<SelectionKey>): void;
}>();

const { columns, data, emitRowClick, rowKey, selection } = toRefs(props);
const slots = useSlots();
const allSelected = computed(() => selection.value.size === data.value.length);
const togglableColumns = reactive(
  columns.value
    .filter((c) => c.isTogglable)
    .map((c) => ({
      [c.colKey]: false,
    }))
);

const selectionText = computed(() => {
  const size = selection.value.size;
  const verb = size > 1 ? "rows" : "row";
  return `${size} ${verb} selected`;
});

function isColVisible(column: Column) {
  return !column.isTogglable || togglableColumns[column.colKey];
}

function toggleRow(row: RowKey) {
  if (!selection.value.delete(row)) {
    selection.value.add(row);
  }

  emit("update:selection", selection.value);
}

function toggleAllRows(cond: boolean) {
  if (!cond || allSelected.value) {
    selection.value.clear();
    emit("update:selection", selection.value);
    return;
  }

  data.value.forEach((d) => selection.value.add(d[rowKey.value]));
  emit("update:selection", selection.value);
}

function onRowClick(row) {
  if (emitRowClick.value) emit("row-click", row[rowKey.value]);
}
</script>

<style scoped>
.selection-bar {
  box-shadow: 0px 0px 1px rgba(0, 0, 0, 0.3),
    0px 1px 3px 1px rgba(0, 0, 0, 0.05), 4px 4px 17px 6px rgba(0, 0, 0, 0.07);
}
</style>
