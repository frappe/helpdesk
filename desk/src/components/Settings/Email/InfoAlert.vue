<template>
  <div
    class="flex items-center gap-2 rounded-md p-2 ring-1 ring-outline-gray-modals"
  >
    <CircleAlert
      class="h-6 w-5 w-min-5 w-max-5 min-h-5 max-w-5 text-ink-blue-2"
    />
    <div class="text-wrap text-xs text-ink-gray-7">
      {{ text }}
      <a
        v-if="link"
        :href="link"
        target="_blank"
        class="text-ink-blue-2 underline"
        >{{ linkLabel }}</a
      >{{ text ? "." : "" }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import CircleAlert from "~icons/lucide/circle-alert";

interface Props {
  text: string;
  link?: string;
  linkLabel?: string;
}

withDefaults(defineProps<Props>(), {
  link: "",
  linkLabel: () => __("here"),
});
</script>
