<template>
  <div class="flex items-center gap-2">
    <Avatar :label="name" :image="image" v-bind="$attrs" />
    <span
      v-if="expand"
      class="truncate"
      :class="{
        'text-gray-900': strong,
        'font-medium': strong,
      }"
    >
      {{ name }}
    </span>
  </div>
</template>
<script setup lang="ts">
import { Avatar } from "frappe-ui";

interface P {
  name: string;
  image?: string;
  expand?: boolean;
  strong?: boolean;
}

withDefaults(defineProps<P>(), {
  image: "",
  expand: false,
  strong: false,
});
</script>
