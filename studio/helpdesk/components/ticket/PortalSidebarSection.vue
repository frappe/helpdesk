<template>
  <div>
    <button
      type="button"
      class="flex w-full items-center gap-1 px-4 py-3.5 text-left"
      :aria-expanded="opened"
      @click="opened = !opened"
    >
      <span class="text-base font-medium text-ink-gray-8">{{ label }}</span>
      <span
        class="lucide-chevron-right size-3.5 text-ink-gray-5 transition-transform"
        :class="{ 'rotate-90': opened }"
      />
    </button>
    <PortalCollapse :open="opened">
      <div class="px-4">
        <slot />
      </div>
    </PortalCollapse>
  </div>
</template>

<script setup lang="ts">
import { provide, ref } from "vue";
import PortalCollapse from "@app/components/common/PortalCollapse.vue";

defineProps<{ label: string }>();

const opened = ref(true);
// Content stays mounted while collapsed, so anything that animates in needs to know when it is shown again.
provide("portalSectionOpen", opened);
</script>
