<template>
  <nav :aria-label="__('Breadcrumb')">
    <ol class="flex min-w-0 flex-wrap items-center gap-x-1 gap-y-0.5 text-sm">
      <li
        v-for="(item, i) in items"
        :key="i"
        class="flex min-w-0 max-w-full items-center gap-1"
      >
        <span
          v-if="i"
          class="lucide-chevron-right size-3.5 shrink-0 text-ink-gray-4"
          aria-hidden="true"
        />
        <PortalLink
          v-if="item.route"
          :to="item.route"
          class="truncate rounded-4 text-ink-gray-5 transition-colors hover:text-ink-gray-7 focus-visible:focus-ring"
        >
          {{ item.label }}
        </PortalLink>
        <span v-else class="truncate text-ink-gray-8" aria-current="page">
          {{ item.label }}
        </span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";
import { __ } from "@helpdesk/shared/translation";
import PortalLink from "@app/components/ui/PortalLink.vue";

defineProps<{ items: { label?: string; route?: RouteLocationRaw }[] }>();
</script>
