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
      :columns="['16px', ...columns]"
      divider="none"
      class="[--list-gap:1rem] [--list-row-padding-x:1rem]"
    >
      <ListHeader
        class="h-9 border-b border-outline-gray-2 bg-surface-gray-2 text-ink-gray-6 [&_[data-slot=list-header-border]]:hidden"
      >
        <ListHeaderCell />
        <slot name="header" />
      </ListHeader>
      <Draggable
        v-model="items"
        :item-key="(item) => item"
        handle=".lucide-grip-vertical"
        v-bind="DRAG_OPTIONS"
        class="divide-y divide-outline-gray-2"
      >
        <template #item="{ element, index }">
          <ListRow class="min-h-12 !items-start py-2.5">
            <ListCell class="h-7 justify-center">
              <span
                class="lucide-grip-vertical size-4 cursor-grab text-ink-gray-4"
                aria-hidden="true"
              />
            </ListCell>
            <slot :item="element" :index="index" />
          </ListRow>
        </template>
      </Draggable>
    </List>
  </div>
</template>

<script setup lang="ts" generic="T">
import {
  List,
  ListCell,
  ListHeader,
  ListHeaderCell,
  ListRow,
} from "frappe-ui/list";
import Draggable from "vuedraggable";
import { DRAG_OPTIONS } from "../utils";

defineProps<{ columns: string[]; emptyText: string }>();
const items = defineModel<T[]>({ required: true });
</script>
