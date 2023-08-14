<template>
  <div
    class="group flex h-10 w-full items-center gap-2 whitespace-nowrap px-4 text-base transition"
    :class="{
      'bg-gray-200': selection.storage.has(data[rowKey]),
      'hover:bg-gray-300': selection.storage.has(data[rowKey]),
      'hover:bg-gray-100': !selection.storage.has(data[rowKey]),
      'cursor-pointer': !!data.onClick,
      ...data.class,
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
      class="flex w-full items-center gap-2"
      @click.prevent="
        () => {
          if (!isObject(data.onClick)) data.onClick.call();
        }
      "
    >
      <div
        v-for="c in columns"
        :key="c.key"
        :class="{
          'text-gray-300': !data[c.key],
        }"
      >
        <div v-if="!hiddenColumns.has(c.key)" :class="[c.width]">
          <div
            :class="['w-max', 'max-w-full', 'truncate', c.align]"
            @click="(event) => filter(event, c)"
          >
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
import { getAssign } from "@/utils";
import { useColumns } from "@/composables/columns";
import { useFilter } from "@/composables/filter";
import { selection } from "./selection";
import { RouterLink } from "vue-router";

interface P {
  id: string;
  checkbox: boolean;
  columns: Column[];
  data: any;
  doctype: string;
  filter: boolean;
  rowKey: string;
}

const props = defineProps<P>();
const id = toRef(props, "id");
const { storage: hiddenColumns } = useColumns(id.value);
const { add: addFilter, apply: applyFilter, fields } = useFilter(props.doctype);

function filter(e: InputEvent, c: Column) {
  if (!props.filter) return;
  const supported = ["Link", "Select"];
  const f__ = fields.find((f) => f.fieldname === c.key);
  if (!f__ || !supported.includes(f__.fieldtype)) return;
  e.preventDefault();
  e.stopPropagation();
  let value = props.data[c.key];
  if (f__.fieldname === "_assign") {
    let assign = getAssign(value);
    if (!assign) return;
    value = assign;
  }
  addFilter({
    fieldname: f__.fieldname,
    operator: "is",
    value: props.data[c.key],
  });
  applyFilter();
}
</script>
