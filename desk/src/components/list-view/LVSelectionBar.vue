<template>
  <transition
    enter-active-class="duration-300 ease-out"
    enter-from-class="transform opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="duration-200 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="transform opacity-0"
  >
    <div
      v-if="selection.storage.size"
      class="fixed inset-x-0 bottom-6 mx-auto flex w-max items-center gap-1 rounded bg-white p-1 text-base shadow"
    >
      <div class="inline-block w-64 pl-2 align-middle text-gray-900">
        {{ selection.storage.size }}
        {{ selection.storage.size < 2 ? singular : plural }} selected
      </div>
      <span class="space-x-2">
        <slot name="actions" :selection="selection.storage" />
      </span>
      <div class="text-gray-300">&#x007C;</div>
      <Button
        :disabled="data?.length === selection.storage.size"
        label="Select all"
        variant="ghost"
        @click="toggle()"
      />
    </div>
  </transition>
</template>

<script setup lang="ts">
import { toRef } from "vue";
import { selection } from "./selection";

interface P {
  data: Array<any>;
  rowKey: string;
  singular?: string;
  plural?: string;
}

const props = withDefaults(defineProps<P>(), {
  singular: "item",
  plural: "items",
});

const data = toRef(props, "data");

function toggle() {
  if (selection.storage.size === data.value.length) {
    selection.storage.clear();
    return;
  }
  data.value.forEach((d) => selection.storage.add(d[props.rowKey]));
}
</script>
