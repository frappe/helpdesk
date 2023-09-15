<template>
  <div class="flex w-full grow flex-col overflow-hidden overflow-x-auto">
    <div
      class="flex h-full w-max min-w-full flex-col overflow-y-hidden text-gray-900"
    >
      <LVEmpty v-if="!resource.data?.length" :message="emptyMsg" />
      <LVHeader
        v-else
        :id="id"
        :checkbox="checkbox"
        :columns="columns"
        :data="resource.data"
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
          :key="row.name"
          :checkbox="checkbox"
          :columns="columns"
          :data="row"
          :doctype="doctype"
          :filter="filter"
          :to="row.onClick"
        >
          <template v-for="(_, n) in $slots" #[n]="d">
            <slot :name="n" v-bind="d" />
          </template>
        </LVRow>
      </div>
    </div>
    <LVNavigation :resource="resource" />
    <LVSelectionBar :data="resource.data || []">
      <template #actions="d">
        <slot name="actions" v-bind="d" />
      </template>
    </LVSelectionBar>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useDebounceFn } from "@vueuse/core";
import { plural } from "pluralize";
import { Column, Resource } from "@/types";
import LVEmpty from "./LVEmpty.vue";
import LVHeader from "./LVHeader.vue";
import LVLoading from "./LVLoading.vue";
import LVNavigation from "./LVNavigation.vue";
import LVRow from "./LVRow.vue";
import LVSelectionBar from "./LVSelectionBar.vue";

interface P {
  id: string;
  columns: Column[];
  doctype: string;
  resource: Resource<Array<Record<string, unknown>>>;
  checkbox?: boolean;
  filter?: boolean;
}

const props = withDefaults(defineProps<P>(), {
  checkbox: false,
  filter: false,
});

const body = ref<HTMLElement | null>(null);
const emptyMsg = computed(() => {
  const s = props.doctype.replace("HD", "").toLowerCase();
  const p = plural(s);
  return `No ${p} found`;
});
const handleScroll = useDebounceFn(() => {
  if (!props.resource.hasNextPage) return;
  const bodyHeight = body.value.scrollHeight;
  const bodyTop = body.value.scrollTop;
  const containerHeight = body.value.clientHeight;
  const scrollPercentage = (bodyTop / (bodyHeight - containerHeight)) * 100;
  if (scrollPercentage >= 90) props.resource.next();
}, 500);
</script>
