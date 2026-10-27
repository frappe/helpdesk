<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <ListView
      v-if="rows.length"
      class="portal-reveal min-h-0 flex-1"
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
      <ListSelectBanner>
        <template #actions="{ selections }">
          <Button
            variant="ghost"
            icon-left="lucide-download"
            :label="__('Export')"
            @click="openExport(selections)"
          />
        </template>
      </ListSelectBanner>
    </ListView>

    <PortalSkeleton v-else-if="loading" class="flex min-h-0 flex-1 flex-col">
      <ListViewSkeleton
        :columns="columns"
        :row-count="Math.min(pageLength, 20)"
      />
    </PortalSkeleton>

    <PortalEmptyState
      v-else-if="!loading"
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
    <ExportModal
      v-model="showExport"
      :row-count="totalCount"
      :all-selected="selectedNames.length === totalCount"
      @update="exportRows"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button } from "frappe-ui";
import ExportModal from "@helpdesk/shared/ExportModal.vue";
import ListViewSkeleton from "@helpdesk/shared/ListViewSkeleton.vue";
import { __ } from "@helpdesk/shared/translation";
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
import PortalEmptyState from "@app/components/ui/PortalEmptyState.vue";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";
import { loadTicketMeta } from "@app/stores/ticketMeta";

// Not at module load: this file ships in public page bundles too.
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

const emit = defineEmits<{
  columnResize: [payload: { key: string; width: string; save: boolean }];
  loadMore: [];
  export: [payload: { exportType: "CSV" | "Excel"; names: string[] | null }];
}>();

const showExport = ref(false);
const selectedNames = ref<string[]>([]);

function openExport(selections: Set<string>) {
  selectedNames.value = [...selections];
  showExport.value = true;
}

function exportRows(form: {
  export_type: "CSV" | "Excel";
  export_all: boolean;
}) {
  showExport.value = false;
  emit("export", {
    exportType: form.export_type,
    names: form.export_all ? null : selectedNames.value,
  });
}
</script>
