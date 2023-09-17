<template>
  <div class="mt-2 flex w-full grow flex-col overflow-hidden overflow-x-auto">
    <div
      class="flex h-full w-max min-w-full flex-col overflow-y-hidden text-gray-900"
    >
      <LVEmpty v-if="!resource.data?.length" :message="emptyMsg" />
      <LVHeader v-else />
      <div
        ref="body"
        class="grow divide-y overflow-y-auto"
        @scroll="() => handleScroll()"
      >
        <LVLoading v-if="resource.loading" />
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
    <LVSelectionBar :data="resource.data || []">
      <template #actions="d">
        <slot name="actions" v-bind="d" />
      </template>
    </LVSelectionBar>
  </div>
  <LVNavigation :resource="resource" />
</template>

<script setup lang="ts">
import { computed, provide, ref } from "vue";
import { useRoute } from "vue-router";
import { useDebounceFn } from "@vueuse/core";
import { plural as pluralize } from "pluralize";
import { Column, Resource } from "@/types";
import {
  CheckboxKey,
  ColumnsKey,
  DocTypeKey,
  FilterKey,
  IdKey,
  PluralKey,
  ResourceKey,
  SingluarKey,
} from "./symbols";
import LVEmpty from "./LVEmpty.vue";
import LVHeader from "./LVHeader.vue";
import LVLoading from "./LVLoading.vue";
import LVNavigation from "./LVNavigation.vue";
import LVRow from "./LVRow.vue";
import LVSelectionBar from "./LVSelectionBar.vue";

interface P {
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

const route = useRoute();
const body = ref<HTMLElement | null>(null);
const singular = computed(() => {
  return props.doctype.replace("HD ", "").toLowerCase().trim();
});
const plural = computed(() => {
  return pluralize(singular.value);
});
const emptyMsg = computed(() => {
  return `No ${plural.value} found`;
});
const id = computed(() => {
  return route.path + "_" + props.doctype;
});
const handleScroll = useDebounceFn(() => {
  if (!props.resource.hasNextPage) return;
  const bodyHeight = body.value.scrollHeight;
  const bodyTop = body.value.scrollTop;
  const containerHeight = body.value.clientHeight;
  const scrollPercentage = (bodyTop / (bodyHeight - containerHeight)) * 100;
  if (scrollPercentage >= 90) props.resource.next();
}, 500);

provide(CheckboxKey, props.checkbox);
provide(ColumnsKey, props.columns);
provide(DocTypeKey, props.doctype);
provide(FilterKey, props.filter);
provide(IdKey, id.value);
provide(PluralKey, plural);
provide(ResourceKey, props.resource);
provide(SingluarKey, singular);
</script>
