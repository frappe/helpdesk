<template>
  <div>
    <CardBase orientation="horizontal" chart-config="" />
  </div>
</template>

<script setup lang="ts">
import CardBase from "@/pages/home/components/CardBase.vue";
import type { LineChart } from "@/types";
import { type PropType } from "vue";

const props = defineProps({
  data: {
    type: Object as PropType<LineChart>,
    required: true,
  },
});
</script>

<style scoped></style>
