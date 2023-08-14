<template>
  <div class="w-full overflow-hidden overflow-x-auto">
    <div
      class="flex h-full w-max min-w-full flex-col overflow-y-hidden text-gray-900"
    >
      <LVEmpty v-if="!loading && !data?.length" :empty-message="emptyMessage" />
      <LVHeader
        v-else
        :id="id"
        :checkbox="checkbox"
        :columns="columns"
        :data="data"
        :row-key="rowKey"
      />
      <div class="divide-y overflow-y-auto">
        <LVLoading
          v-if="loading"
          :id="id"
          :columns="columns"
          :checkbox="checkbox"
        />
        <LVRow
          v-for="row in data"
          v-else
          :id="id"
          :key="row[rowKey]"
          :checkbox="checkbox"
          :columns="columns"
          :data="row"
          :doctype="doctype"
          :filter="filter"
          :row-key="rowKey"
          :to="row.onClick"
        >
          <template v-for="(_, n) in $slots" #[n]="d">
            <slot :name="n" v-bind="d" />
          </template>
        </LVRow>
      </div>
    </div>
    <LVSelectionBar :data="data || []" :row-key="rowKey">
      <template #actions="d">
        <slot name="actions" v-bind="d" />
      </template>
    </LVSelectionBar>
  </div>
</template>

<script setup lang="ts">
import { Column } from "@/types";
import LVEmpty from "./LVEmpty.vue";
import LVHeader from "./LVHeader.vue";
import LVLoading from "./LVLoading.vue";
import LVRow from "./LVRow.vue";
import LVSelectionBar from "./LVSelectionBar.vue";

interface P {
  id: string;
  columns: Column[];
  doctype: string;
  rowKey: string;
  checkbox?: boolean;
  data?: Record<string, any>[];
  emptyMessage?: string;
  filter?: boolean;
  loading?: boolean;
}

withDefaults(defineProps<P>(), {
  checkbox: false,
  emptyMessage: "No records",
  filter: false,
  loading: false,
});
</script>
