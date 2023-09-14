<template>
  <div class="w-full overflow-hidden overflow-x-auto">
    <div
      class="flex h-full w-max min-w-full flex-col overflow-y-hidden text-gray-900"
    >
      <LVEmpty
        v-if="!resource.loading && !resource.data?.length"
        :empty-message="emptyMessage"
      />
      <LVHeader
        v-else
        :id="id"
        :checkbox="checkbox"
        :columns="columns"
        :data="resource.data"
        :row-key="rowKey"
      />
      <div
        ref="body"
        class="grow divide-y overflow-y-auto"
        @scroll="() => handleScroll()"
      >
        <LVLoading
          v-if="resource.loading"
          :id="id"
          :columns="columns"
          :checkbox="checkbox"
        />
        <LVRow
          v-for="row in resource.data"
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
      <LVNavigation :resource="resource" />
    </div>
    <LVSelectionBar :data="resource.data || []" :row-key="rowKey">
      <template #actions="d">
        <slot name="actions" v-bind="d" />
      </template>
    </LVSelectionBar>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Column, Resource } from "@/types";
import LVEmpty from "./LVEmpty.vue";
import LVHeader from "./LVHeader.vue";
import LVLoading from "./LVLoading.vue";
import LVNavigation from "./LVNavigation.vue";
import LVRow from "./LVRow.vue";
import LVSelectionBar from "./LVSelectionBar.vue";
import { useDebounceFn } from "@vueuse/core";

interface P {
  id: string;
  columns: Column[];
  doctype: string;
  rowKey: string;
  resource: Resource<Array<Record<string, unknown>>>;
  checkbox?: boolean;
  emptyMessage?: string;
  filter?: boolean;
}

const props = withDefaults(defineProps<P>(), {
  checkbox: false,
  emptyMessage: "No records",
  filter: false,
});

const body = ref<HTMLElement | null>(null);
const handleScroll = useDebounceFn(() => {
  const bodyHeight = body.value.scrollHeight;
  const bodyTop = body.value.scrollTop;
  const containerHeight = body.value.clientHeight;
  const scrollPercentage = (bodyTop / (bodyHeight - containerHeight)) * 100;
  if (scrollPercentage >= 90) props.resource.next();
}, 500);
</script>
