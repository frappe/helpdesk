<template>
  <div class="space-y-2">
    <div class="text-lg font-medium text-gray-900">{{ title }}</div>
    <div class="flex flex-wrap items-center gap-2 text-base">
      <div
        v-for="(item, index) in items"
        :key="item.key"
        class="flex items-center gap-2"
      >
        <div class="text-gray-800">{{ item.label }}</div>
        <SearchComplete
          placeholder="Any"
          :doctype="item.doctype"
          :value="doc[item.key]"
          @change="(v) => onChange(item.key, v.value)"
        />
        <span v-if="index + 1 < items.length" class="text-gray-600"> and </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRef } from "vue";
import SearchComplete from "@/components/SearchComplete.vue";

type Item = {
  label: string;
  doctype: string;
  key: string;
};

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  items: {
    type: Array<Item>,
    required: true,
  },
  doc: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits<{
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (event: "update:doc", value: any): void;
}>();

const doc = toRef(props, "doc");

function onChange(key: string, value: string) {
  emit("update:doc", {
    ...doc.value,
    [key]: value,
  });
}
</script>
