<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div
      v-if="loading && !rows.length"
      class="flex h-full w-full items-center justify-center"
    >
      <LoadingIndicator :scale="8" />
    </div>

    <!-- One stacked row per ticket on a phone, where table columns leave the subject no room. -->
    <div
      v-else-if="rows.length && compact"
      class="min-h-0 flex-1 overflow-y-auto"
    >
      <button
        v-for="row in rows"
        :key="row.name"
        type="button"
        class="flex w-full flex-col gap-1.5 border-b border-outline-gray-1 px-4 py-3 text-left text-base text-ink-gray-8 transition-colors active:bg-surface-gray-2"
        @click="onRowClick?.(row)"
      >
        <span class="flex w-full min-w-0 items-baseline gap-3">
          <component :is="cell('subject', row)" />
          <span class="shrink-0 text-ink-gray-5">
            <component :is="cell('creation', row)" />
          </span>
        </span>
        <span class="flex w-full min-w-0 items-center gap-3 text-ink-gray-6">
          <span class="flex min-w-0 flex-1">
            <component :is="cell('status', row)" />
          </span>
          <span class="shrink-0">
            <component :is="cell('name', row)" />
          </span>
        </span>
      </button>
    </div>

    <ListView
      v-else-if="rows.length"
      class="min-h-0 flex-1"
      :columns="columns"
      :rows="rows"
      row-key="name"
      :options="{
        selectable: true,
        showTooltip: false,
        resizeColumn: true,
        onRowClick,
      }"
    >
      <ListHeader class="mx-3 sm:mx-5">
        <ListHeaderItem
          v-for="column in columns"
          :key="column.key"
          :item="column"
          @columnWidthUpdated="(payload) => emit('columnResize', payload)"
        />
      </ListHeader>
      <ListRows class="mx-3 sm:mx-5">
        <ListRow
          v-for="row in rows"
          :key="row.name"
          :row="row"
          v-slot="{ column, item }"
          class="truncate text-base"
        >
          <ListRowItem :item="item" :column="column" :row="row">
            <component
              :is="column.cell({ row, item })"
              v-if="column.cell"
              :key="column.key"
            />
          </ListRowItem>
        </ListRow>
      </ListRows>
      <ListSelectBanner />
    </ListView>

    <PortalEmptyState
      v-else
      class="pointer-events-none flex-1"
      icon="ticket"
      :title="emptyState.title"
      :description="emptyState.description"
    />

    <div v-if="rows.length" class="border-t px-3 py-2 sm:px-5">
      <ListFooter
        v-model="pageLength"
        :options="{ rowCount, totalCount, pageLengthOptions }"
        @loadMore="emit('loadMore')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { LoadingIndicator } from "frappe-ui";
import {
  ListFooter,
  ListHeader,
  ListHeaderItem,
  ListRow,
  ListRowItem,
  ListRows,
  ListSelectBanner,
  ListView,
} from "frappe-ui/experimental";
import PortalEmptyState from "@app/components/common/PortalEmptyState.vue";
import { loadTicketMeta } from "@app/stores/ticketMeta";

// Not at module load: this file ships in the public page bundles too.
loadTicketMeta();

const props = withDefaults(
  defineProps<{
    columns?: any[];
    rows?: any[];
    loading?: boolean;
    rowCount?: number;
    totalCount?: number;
    pageLengthOptions?: number[];
    emptyState?: { title: string; description?: string };
    onRowClick?: (row: any) => void;
    compact?: boolean;
  }>(),
  {
    columns: () => [],
    rows: () => [],
    loading: false,
    rowCount: 0,
    totalCount: 0,
    pageLengthOptions: () => [],
    emptyState: () => ({ title: "" }),
    compact: false,
  }
);

const pageLength = defineModel<number>("pageLength", { default: 20 });

const emit = defineEmits<{
  columnResize: [payload: { key: string; width: string; save: boolean }];
  loadMore: [];
}>();

function cell(key: string, row: any) {
  const column = props.columns.find((column) => column.key === key);
  return column?.cell?.({ row, item: row[key] }) ?? null;
}
</script>
