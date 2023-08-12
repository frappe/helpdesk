<template>
  <div
    class="group flex h-10 w-full items-center space-x-2 whitespace-nowrap px-5 text-base transition"
    :class="{
      'bg-gray-200': selection.storage.has(data[rowKey]),
      'hover:bg-gray-300': selection.storage.has(data[rowKey]),
      'hover:bg-gray-100': !selection.storage.has(data[rowKey]),
      'cursor-pointer': !!data.onClick,
    }"
  >
    <FormControl
      v-if="checkbox"
      type="checkbox"
      :model-value="selection.storage.has(data[rowKey])"
      @update:model-value="selection.toggle(data[rowKey])"
    />
    <component
      :is="isObject(data.onClick) ? RouterLink : 'span'"
      as="template"
      :to="data.onClick"
      class="flex w-full items-center space-x-2"
      @click.prevent="data.onClick.call()"
    >
      <div
        v-for="c in columns"
        :key="c.key"
        :class="{
          'text-gray-300': !data[c.key],
        }"
      >
        <div v-if="!hiddenColumns.has(c.key)" :class="[c.width]">
          <div :class="['w-max', 'max-w-full', 'truncate', c.align]">
            <slot :name="c.key" :data="data">
              {{ data[c.key] || "⸺" }}
            </slot>
          </div>
        </div>
      </div>
    </component>
  </div>
</template>

<script setup lang="ts">
import { toRef } from "vue";
import { FormControl } from "frappe-ui";
import { isObject } from "lodash";
import { Column } from "@/types";
import { useColumns } from "@/composables/columns";
import { selection } from "./selection";
import { RouterLink } from "vue-router";

interface P {
  id: string;
  checkbox: boolean;
  columns: Column[];
  data: any;
  rowKey: string;
}

const props = defineProps<P>();
const id = toRef(props, "id");
const { storage: hiddenColumns } = useColumns(id.value);
</script>
