<template>
  <div v-if="isEmoji(icon)" v-bind="$attrs">
    {{ icon }}
  </div>
  <SpriteIcon
    v-else-if="typeof icon == 'string'"
    :name="icon.replace('lucide-', '')"
    v-bind="$attrs"
  />
  <component v-else :is="icon" v-bind="$attrs" />
</template>
<script setup>
import { isEmoji } from "@/utils";
// Sprite, not a `lucide-*` class: these names come from stored view icons, and
// Tailwind only emits CSS for class names it can see in source.
import { Icon as SpriteIcon } from "frappe-ui/experimental";

const props = defineProps({
  icon: {
    type: [String, Object],
    required: true,
  },
});
</script>
