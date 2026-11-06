<template>
  <!-- Header bar and 40px rows share one column grid, so the bars sit where the columns will. -->
  <div class="flex min-h-0 flex-1 flex-col">
    <!-- w-max: narrow screens clip the columns, not squeeze them. -->
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div
        class="mx-3 flex w-max min-w-[calc(100%-1.5rem)] flex-col sm:mx-5 sm:min-w-[calc(100%-2.5rem)]"
      >
        <div
          class="mb-2 grid h-[34px] shrink-0 items-center gap-4 rounded-4 bg-surface-gray-2 px-2"
          :style="{ gridTemplateColumns }"
        >
          <Skeleton v-if="selectable" :class="[BLOCK, CHECKBOX]" />
          <Skeleton
            v-for="(column, index) in shownColumns"
            :key="column.key"
            :class="[BLOCK, 'h-[0.6em] min-w-6 max-w-16 rounded-full text-sm']"
            :style="{ width: `${50 + ((index * 17) % 30)}%` }"
          />
        </div>
        <div v-for="row in rowCount" :key="row" class="shrink-0">
          <div
            class="grid h-10 items-center gap-4 px-2"
            :style="{ gridTemplateColumns }"
          >
            <Skeleton v-if="selectable" :class="[BLOCK, CHECKBOX]" />
            <Skeleton
              v-for="(column, index) in shownColumns"
              :key="column.key"
              :class="[BLOCK, 'h-[0.6em] min-w-8 rounded-full text-base']"
              :style="{ width: `${40 + ((row * 7 + index * 13) % 45)}%` }"
            />
          </div>
          <div
            v-if="row < rowCount"
            class="mx-2 h-px border-t border-outline-gray-1"
          />
        </div>
      </div>
    </div>
    <div
      v-if="footer"
      class="flex h-[49px] shrink-0 items-center justify-between border-t px-3 sm:px-5"
    >
      <Skeleton :class="[BLOCK, 'h-7 w-[104px] rounded-[8px]']" />
      <Skeleton :class="[BLOCK, 'h-[0.6em] w-16 rounded-full text-base']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Skeleton } from "frappe-ui";

const props = withDefaults(
  defineProps<{
    columns: { key: string; width?: number | string }[];
    rowCount?: number;
    selectable?: boolean;
    footer?: boolean;
  }>(),
  { rowCount: 20, selectable: true, footer: true }
);

const BLOCK = "motion-reduce:animate-none";
const CHECKBOX = "size-3.5 rounded-[4px]";
// Before the first response a list knows no columns yet: a wide subject, then narrower ones.
const PLACEHOLDER_COLUMNS = [3, 1, 1, 1, 1].map((width, index) => ({
  key: String(index),
  width,
}));

const shownColumns = computed(() =>
  props.columns.length ? props.columns : PLACEHOLDER_COLUMNS
);

// Checkbox, then each column's width; plain numbers become `fr`.
const gridTemplateColumns = computed(() =>
  [
    ...(props.selectable ? ["14px"] : []),
    ...shownColumns.value.map((column) =>
      typeof (column.width || 1) === "number"
        ? `${column.width || 1}fr`
        : column.width
    ),
  ].join(" ")
);
</script>
