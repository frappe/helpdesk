<template>
  <!-- Mirrors the view controls block for block, so nothing moves when they load. -->
  <template v-if="!isMobileView">
    <div class="flex flex-1 items-center gap-2 py-1 pe-4 ps-1 -ms-1">
      <Skeleton v-for="index in 3" :key="index" :class="[BLOCK, 'w-36']" />
    </div>
    <div class="-ms-2 h-5 border-s" />
    <div class="flex h-full items-start justify-end gap-2 py-1 ps-0.5">
      <Skeleton :class="[BLOCK, 'w-7']" />
      <Skeleton :class="[BLOCK, 'w-[73px]']" />
      <Skeleton :class="[BLOCK, 'w-36']" />
      <Skeleton v-if="groupBy" :class="[BLOCK, 'w-[81px]']" />
      <Skeleton v-if="columnSetting" :class="[BLOCK, 'w-[98px]']" />
    </div>
  </template>
  <div v-else class="flex w-full items-center justify-between">
    <Skeleton :class="[BLOCK, 'w-[73px]']" />
    <div class="flex items-center gap-2">
      <Skeleton :class="[BLOCK, 'w-7']" />
      <Skeleton :class="[BLOCK, 'w-7']" />
      <Skeleton v-if="groupBy" :class="[BLOCK, 'w-7']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Skeleton } from "frappe-ui";

defineProps<{
  isMobileView: boolean;
  groupBy: boolean;
  columnSetting: boolean;
}>();

const BLOCK = "h-7 shrink-0 rounded-[8px] motion-reduce:animate-none";
</script>
