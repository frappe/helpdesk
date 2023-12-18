<template>
  <div class="flex min-w-0 items-center text-ellipsis whitespace-nowrap">
    <template v-for="(item, i) in items" :key="item.label">
      <router-link
        class="flex items-center rounded px-0.5 py-1 text-lg font-medium text-gray-600 transition-all duration-300 ease-in-out first:pl-0 last:text-gray-900 hover:text-gray-700 last:hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
        :to="item.route || ''"
      >
        <slot name="prefix" :item="item" />
        <span v-if="i == items.length - 1" @click="clickToCopy(item.name)">{{
          item.label
        }}</span>
        <span v-else>{{ item.label }}</span>
      </router-link>
      <span v-if="i != items.length - 1" class="mx-0.5 text-base text-gray-500">
        /
      </span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { createToast } from "@/utils";

interface Item {
  label: string;
  route: string;
}

interface P {
  items: Item[];
}

function clickToCopy(text: string) {
  navigator.clipboard.writeText(text);
  createToast({
    title: "Ticket ID copied to clipboard",
    icon: "check",
    iconClasses: "text-green-500",
  });
}

defineProps<P>();
</script>
