<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <List
      v-if="rows.length || loading"
      class="min-h-0 flex-1"
      :columns="columns"
      :rows="rows"
      row-key="name"
      :loading="loading"
      :row-link="(row) => ROUTES.ticket(row.name as string)"
      v-model:sort="sort"
      @column-resize="(payload) => emit('columnResize', payload)"
    >
      <template #cell="{ row, column }">
        <component
          :is="column.cell({ row, item: row[column.fieldname] })"
          v-if="column.cell"
        />
      </template>
    </List>

    <PortalEmptyState
      v-else
      class="pointer-events-none flex-1"
      icon="ticket"
      :title="emptyState.title"
      :description="emptyState.description"
    />

    <div v-if="rows.length" class="border-t px-3 py-2 sm:px-5">
      <ListFooter
        v-model:page-size="pageLength"
        :row-count="rowCount"
        :total-count="totalCount"
        has-counts
        :page-size-options="pageLengthOptions"
        @load-more="emit('loadMore')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { List, ListFooter } from "@framework/ui/experimental/List";
import type { ColumnResize } from "@framework/ui/experimental/List";
import type { Sort } from "@framework/ui/SortBy";
import PortalEmptyState from "@app/components/common/PortalEmptyState.vue";
import { ROUTES } from "@app/routes";
import { loadTicketMeta } from "@app/stores/ticketMeta";

// Here, not at module load: this file ships in the public page bundles too.
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
  }>(),
  {
    columns: () => [],
    rows: () => [],
    loading: false,
    rowCount: 0,
    totalCount: 0,
    pageLengthOptions: () => [],
    emptyState: () => ({ title: "" }),
  }
);

const pageLength = defineModel<number>("pageLength", { default: 20 });
const sort = defineModel<Sort[]>("sort", { default: () => [] });

const emit = defineEmits<{
  (e: "columnResize", payload: ColumnResize): void;
  (e: "loadMore"): void;
}>();
</script>
