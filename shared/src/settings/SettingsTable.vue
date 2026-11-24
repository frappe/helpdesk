<template>
  <div
    class="flex flex-col overflow-hidden rounded-5 border border-outline-gray-2 text-sm"
  >
    <p
      v-if="!items.length"
      class="my-1 flex min-h-11 items-center justify-center px-3 text-center text-p-base text-ink-gray-6 sm:min-h-10"
    >
      {{ emptyText }}
    </p>
    <List
      v-else
      :columns="['16px', ...columns.map((column) => column.width), '32px']"
      divider="none"
      class="[--list-gap:1rem] [--list-row-padding-x:1rem]"
    >
      <ListHeader
        class="h-9 border-b border-outline-gray-2 bg-surface-gray-2 text-ink-gray-6 [&_[data-slot=list-header-border]]:hidden"
      >
        <ListHeaderCell />
        <ListHeaderCell
          v-for="column in columns"
          :key="column.key"
          :class="column.class"
        >
          {{ column.label }}
        </ListHeaderCell>
        <ListHeaderCell />
      </ListHeader>
      <Draggable
        v-model="items"
        :item-key="(item) => item"
        handle=".lucide-grip-vertical"
        v-bind="DRAG_OPTIONS"
        class="divide-y divide-outline-gray-2"
      >
        <template #item="{ element, index }">
          <ListRow
            class="min-h-12 !items-start py-2.5 [&>[data-slot=list-cell]]:min-h-7"
          >
            <ListCell class="justify-center">
              <span
                class="lucide-grip-vertical size-4 cursor-grab text-ink-gray-4"
                aria-hidden="true"
              />
            </ListCell>
            <ListCell
              v-for="column in columns"
              :key="column.key"
              :class="column.class"
            >
              <slot :name="column.key" :item="element" :index="index" />
            </ListCell>
            <ListCell>
              <Dropdown
                align="end"
                :options="optionsFor(index)"
                @update:open="(open) => open && (isConfirmingDelete = false)"
              >
                <Button
                  variant="ghost"
                  icon="lucide-more-horizontal"
                  :label="
                    __('Options for {0}', [rowLabel(element) || __('Untitled')])
                  "
                />
              </Dropdown>
            </ListCell>
          </ListRow>
        </template>
      </Draggable>
    </List>
  </div>
</template>

<script setup lang="ts" generic="T">
import { Button, Dropdown } from "frappe-ui";
import {
  List,
  ListCell,
  ListHeader,
  ListHeaderCell,
  ListRow,
} from "frappe-ui/list";
import { ref } from "vue";
import Draggable from "vuedraggable";
import { __ } from "../translation";
import { DRAG_OPTIONS, rowOptions } from "./settingsTable";

const props = defineProps<{
  columns: { key: string; label: string; width: string; class?: string }[];
  emptyText: string;
  rowLabel: (item: T) => string;
  remove?: { label: string; icon: string };
}>();
const items = defineModel<T[]>({ required: true });

const isConfirmingDelete = ref(false);
const optionsFor = (index: number) =>
  rowOptions(items, index, isConfirmingDelete, props.remove);
</script>
