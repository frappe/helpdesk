<template>
  <div class="flex items-center justify-between py-3" v-bind:class="$attrs">
    <div class="flex items-center space-x-3 w-4/5">
      <Avatar :image="agent.user_image" :label="agent.agent_name" size="xl" />
      <div>
        <div class="text-base font-semibold text-ink-gray-8">
          {{ agent.agent_name }}
        </div>
        <div class="text-base text-ink-gray-6 mt-1">
          {{ agent.name }}
        </div>
      </div>
    </div>
    <!-- slot her -->
    <slot name="right" />
  </div>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";

defineProps({
  agent: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped></style>
