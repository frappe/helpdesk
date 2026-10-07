<template>
  <Button variant="outline" :label="label" @click="emit('click')">
    <template #prefix>
      <span :class="['shrink-0 rounded-full', MILESTONE_DOT_CLASSES[state]]" />
    </template>
  </Button>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import { MILESTONE_DOT_CLASSES, type MilestoneState } from "./milestoneDots";

withDefaults(defineProps<{ label?: string; state?: MilestoneState }>(), {
  label: "",
  state: "done",
});

const emit = defineEmits<{ click: [] }>();
</script>
