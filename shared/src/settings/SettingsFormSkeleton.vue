<template>
  <div class="flex flex-col" aria-busy="true">
    <span class="sr-only" role="status">{{ __("Loading") }}</span>
    <div class="flex flex-col gap-6">
      <div
        v-for="i in toggles"
        :key="i"
        class="flex items-center justify-between gap-4"
      >
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <div class="flex h-[19px] items-center">
            <Skeleton
              :class="[BLOCK, 'h-2.5 rounded-full']"
              :style="{ width: `${7 + (i % 3) * 2}rem` }"
            />
          </div>
          <div class="flex h-[19.5px] items-center">
            <Skeleton
              :class="[BLOCK, 'h-2 w-full max-w-[22rem] rounded-full']"
            />
          </div>
        </div>
        <Skeleton :class="[BLOCK, 'h-4 w-[26px] shrink-0 rounded-full']" />
      </div>
    </div>
    <!-- Knowledge Base form: pins, banner, links. -->
    <div v-for="i in sections" :key="i" class="mt-8 flex flex-col gap-2">
      <Skeleton :class="[BLOCK, 'h-2.5 w-28 rounded-full']" />
      <Skeleton :class="[BLOCK, 'h-2 w-3/4 rounded-full']" />
      <Skeleton :class="[BLOCK, 'mt-2 h-24 w-full rounded-[10px]']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Skeleton } from "frappe-ui";
import { __ } from "../translation";

withDefaults(defineProps<{ toggles?: number; sections?: number }>(), {
  toggles: 4,
  sections: 0,
});

const BLOCK = "motion-reduce:animate-none";
</script>
