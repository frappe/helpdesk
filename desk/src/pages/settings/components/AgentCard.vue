<template>
  <div class="flex items-center justify-between py-2" v-bind:class="$attrs">
    <div class="flex items-center space-x-3 w-4/5">
      <Avatar :image="agent.user_image" :label="agent.agent_name" size="xl" />
      <div>
        <div class="flex items-center gap-2">
          <p class="text-base">
            {{ agent.agent_name }}
          </p>
          <Badge
            v-if="showStatus"
            :label="'Inactive'"
            :theme="'gray'"
            :class="
              showStatus && !agent.is_active ? 'opacity-100' : 'opacity-0'
            "
            variant="subtle"
          />
        </div>
        <div class="text-base text-ink-gray-6 mt-1">
          {{ agent.name }}
        </div>
      </div>
    </div>
    <!-- slot here -->
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
  showStatus: {
    type: Boolean,
    default: false,
  },
});
</script>

<style scoped></style>
