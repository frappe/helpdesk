<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div
      v-if="loading && !rows.length"
      class="flex h-full w-full items-center justify-center"
    >
      <LoadingIndicator :scale="8" />
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
          class="truncate text-base row"
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

    <KbEmptyState
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
// The KB portal's ticket table. Deliberately a mirror of the agent portal's
// `desk/src/components/ListViewBuilder.vue` — same frappe-ui primitives, same
// gutters (`mx-5`), same footer chrome — so both list views read as one design.
// It draws nothing itself: every cell comes from its column's `cell()`, the way
// ListViewBuilder defers to `listCell`.
import KbEmptyState from "@app/components/KbEmptyState.vue";
import { loadTicketMeta } from "@app/components/ticketCells";
import {
  ListFooter,
  ListHeader,
  ListHeaderItem,
  ListRow,
  ListRowItem,
  ListRows,
  ListSelectBanner,
  ListView,
  LoadingIndicator,
} from "frappe-ui";

// The status colours and priority levels the cells draw with. Asked for here
// rather than at module load: this file ships in every page bundle, including the
// public ones a guest sees.
loadTicketMeta();

withDefaults(
  defineProps<{
    columns?: any[];
    rows?: any[];
    loading?: boolean;
    rowCount?: number;
    totalCount?: number;
    pageLengthOptions?: number[];
    emptyState?: { title: string; description?: string };
    onRowClick?: (row: any) => void;
  }>(),
  {
    columns: () => [],
    rows: () => [],
    loading: false,
    rowCount: 0,
    totalCount: 0,
    pageLengthOptions: () => [20, 50, 100],
    emptyState: () => ({ title: "No tickets found" }),
  }
);

const pageLength = defineModel<number>("pageLength", { default: 20 });

const emit = defineEmits<{
  (
    e: "columnResize",
    payload: { key: string; width: string; save: boolean }
  ): void;
  (e: "loadMore"): void;
}>();
</script>
