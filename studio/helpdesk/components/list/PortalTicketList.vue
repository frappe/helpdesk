<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <!-- Skeleton reuses the table so headings and rows land in place. -->
    <ListView
      v-if="shownRows.length"
      class="min-h-0 flex-1"
      :class="isSkeleton ? 'pointer-events-none' : 'portal-reveal'"
      v-bind="skeletonAttrs"
      :columns="shownColumns"
      :rows="shownRows"
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
          v-for="row in shownRows"
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
    <div
      v-else-if="isSkeleton"
      class="flex h-[45px] items-center justify-between border-t px-3 sm:px-5"
      aria-hidden="true"
    >
      <Skeleton class="h-7 w-[104px] rounded-6 motion-reduce:animate-none" />
      <Skeleton class="h-2.5 w-14 rounded-full motion-reduce:animate-none" />
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
import { computed, h, ref } from "vue";
import { Button, Skeleton } from "frappe-ui";
import ExportModal from "@helpdesk/shared/ExportModal.vue";
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

function exportRows(form: { export_type: "CSV" | "Excel"; export_all: boolean }) {
  showExport.value = false;
  emit("export", {
    exportType: form.export_type,
    names: form.export_all ? null : selectedNames.value,
  });
}

const SKELETON_ROWS = Array.from({ length: 20 }, (_, index) => ({
  name: `skeleton-${index}`,
  index,
}));
const WIDTHS = [72, 58, 84, 64, 90, 52, 78, 68];

const isSkeleton = computed(() => props.loading && !props.rows.length);
const shownRows = computed(() =>
  isSkeleton.value ? SKELETON_ROWS : props.rows
);
const shownColumns = computed(() =>
  isSkeleton.value
    ? props.columns.map((column) => ({
        ...column,
        cell: ({ row }) => placeholder(row, column.key),
      }))
    : props.columns
);
const skeletonAttrs = computed(() =>
  isSkeleton.value
    ? { "aria-busy": "true", "aria-label": __("Loading tickets") }
    : {}
);

function placeholder(row: { index: number }, key: string) {
  const share = WIDTHS[(row.index + key.length) % WIDTHS.length];
  const width =
    key === "subject"
      ? `${Math.max(share, 45)}%`
      : key === "name"
      ? "2.5rem"
      : `${share}%`;
  return h(Skeleton, {
    class: [
      "h-2.5 rounded-full motion-reduce:animate-none",
      key === "status" ? "max-w-[6rem]" : "max-w-[16rem]",
    ],
    style: { width },
  });
}
</script>
