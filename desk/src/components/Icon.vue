<template>
  <div v-if="isEmoji(icon)" v-bind="$attrs">
    {{ icon }}
  </div>
  <span
    v-else-if="typeof icon == 'string' && icon.startsWith('lucide-')"
    :class="icon"
    v-bind="$attrs"
  />
  <span
    v-else-if="typeof icon == 'string'"
    :class="`lucide-${icon}`"
    v-bind="$attrs"
  />
  <component v-else :is="icon" v-bind="$attrs" />
</template>
<script setup>
import { isEmoji } from "@/utils";

const props = defineProps({
  icon: {
    type: [String, Object],
    required: true,
  },
});
</script>
