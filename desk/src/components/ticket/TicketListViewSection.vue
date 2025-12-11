<template>
  <div>
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @empty-state-action="emit('empty-action')"
      @row-click="(row) => emit('row-click', row)"
    />
  </div>
</template>

<script setup lang="ts">
import { ListViewBuilder } from "@/components";
import { ref, toRefs } from "vue";

const props = defineProps<{
  options: any;
}>();

const emit = defineEmits<{
  (e: "empty-action"): void;
  (e: "row-click", row: string): void;
}>();

const listViewRef = ref<any>(null);
const { options } = toRefs(props);

defineExpose({
  listViewRef,
});
</script>

