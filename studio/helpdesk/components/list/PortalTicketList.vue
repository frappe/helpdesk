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

    <!-- Header bar and 40px rows share one column grid. -->
    <PortalSkeleton v-else-if="loading" class="flex min-h-0 flex-1 flex-col">
      <!-- w-max: narrow screens clip the columns, not squeeze them. -->
      <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div
          class="mx-3 flex w-max min-w-[calc(100%-1.5rem)] flex-col sm:mx-5 sm:min-w-[calc(100%-2.5rem)]"
        >
          <div
            class="mb-2 grid h-[34px] shrink-0 items-center gap-4 rounded-4 bg-surface-gray-2 px-2"
            :style="{ gridTemplateColumns }"
          >
            <Skeleton
              class="size-3.5 rounded-[4px] motion-reduce:animate-none"
            />
            <Skeleton
              v-for="(column, i) in columns"
              :key="column.key"
              class="h-[0.6em] min-w-6 max-w-16 rounded-full text-sm motion-reduce:animate-none"
              :style="{ width: `${50 + ((i * 17) % 30)}%` }"
            />
          </div>
          <div
            v-for="row in Math.min(pageLength, 20)"
            :key="row"
            class="shrink-0"
          >
            <div
              class="grid h-10 items-center gap-4 px-2"
              :style="{ gridTemplateColumns }"
            >
              <Skeleton
                class="size-3.5 rounded-[4px] motion-reduce:animate-none"
              />
              <Skeleton
                v-for="(column, i) in columns"
                :key="column.key"
                class="h-[0.6em] min-w-8 rounded-full text-base motion-reduce:animate-none"
                :style="{ width: `${40 + ((row * 7 + i * 13) % 45)}%` }"
              />
            </div>
            <div
              v-if="row < Math.min(pageLength, 20)"
              class="mx-2 h-px border-t border-outline-gray-1"
            />
          </div>
        </div>
      </div>
      <div
        class="flex h-[49px] shrink-0 items-center justify-between border-t px-3 sm:px-5"
      >
        <Skeleton
          class="h-7 w-[104px] rounded-[8px] motion-reduce:animate-none"
        />
        <Skeleton
          class="h-[0.6em] w-16 rounded-full text-base motion-reduce:animate-none"
        />
      </div>
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
import { computed, ref } from "vue";
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

// Checkbox, then each column's width; plain numbers become `fr`.
const gridTemplateColumns = computed(() =>
  [
    "14px",
    ...props.columns.map((column) =>
      typeof (column.width || 1) === "number"
        ? `${column.width || 1}fr`
        : column.width
    ),
  ].join(" ")
);

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
