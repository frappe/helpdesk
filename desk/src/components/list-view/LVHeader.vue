<template>
  <div class="mx-5 rounded bg-gray-100 py-2 px-2.5 text-sm text-gray-600">
    <div class="flex w-full items-center gap-2">
      <FormControl
        v-if="checkbox"
        type="checkbox"
        :model-value="data?.length === selection.storage.size"
        @update:model-value="toggle()"
      />
      <div v-for="c in columns" :key="c.key">
        <div v-if="!hiddenColumns.has(c.key)" :class="[c.width]">
          <Icon
            v-if="c.icon"
            :icon="c.icon"
            class="h-4 w-4"
            :class="[c.align]"
          />
          <span v-else :class="[c.align]">{{ c.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRef } from "vue";
import { Icon } from "@iconify/vue";
import { Column } from "@/types";
import { useColumns } from "@/composables/columns";
import { selection } from "./selection";

interface P {
  id: string;
  checkbox: boolean;
  columns: Column[];
  data: Array<any>;
  rowKey: string;
}

const props = defineProps<P>();

const data = toRef(props, "data");
const id = toRef(props, "id");
const { storage: hiddenColumns } = useColumns(id.value);

function toggle() {
  if (selection.storage.size === data.value.length) {
    selection.storage.clear();
    return;
  }
  data.value.forEach((d) => selection.storage.add(d[props.rowKey]));
}
</script>
