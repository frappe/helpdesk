<template>
  <div class="space-y-11" aria-busy="true">
    <!-- Real headings: only the rows wait for data. -->
    <section v-for="section in sections" :key="section.title">
      <h2 class="text-md-semibold text-ink-gray-8">{{ section.title }}</h2>
      <div class="mt-2 divide-y divide-outline-gray-1">
        <div
          v-for="i in section.rows || 0"
          :key="`row-${i}`"
          class="flex items-center justify-between gap-8 py-3.5"
        >
          <div class="flex min-w-0 flex-1 flex-col gap-1">
            <div class="flex h-[17px] items-center">
              <Skeleton
                :class="[BLOCK, 'h-2.5 rounded-full']"
                :style="{ width: `${7 + (i % 3) * 2}rem` }"
              />
            </div>
            <div class="flex h-5 items-center">
              <Skeleton
                :class="[BLOCK, 'h-2 w-full max-w-[22rem] rounded-full']"
              />
            </div>
          </div>
          <Skeleton :class="[BLOCK, 'h-4 w-[26px] shrink-0 rounded-full']" />
        </div>
        <!-- A titled block over a box, e.g. pinned categories or the banner. -->
        <div
          v-for="(height, i) in section.panels || []"
          :key="`panel-${i}`"
          class="flex flex-col gap-1 py-3.5"
        >
          <div class="flex h-[17px] items-center">
            <Skeleton :class="[BLOCK, 'h-2.5 w-28 rounded-full']" />
          </div>
          <div class="flex h-5 items-center">
            <Skeleton :class="[BLOCK, 'h-2 w-3/4 rounded-full']" />
          </div>
          <Skeleton
            :class="[BLOCK, 'mt-2 w-full rounded-[10px]']"
            :style="{ height: `${height}px` }"
          />
        </div>
      </div>
    </section>
    <!-- Last: first, it would take the sections' top margin. -->
    <span class="sr-only" role="status">{{ __("Loading") }}</span>
  </div>
</template>

<script setup lang="ts">
import { Skeleton } from "frappe-ui";
import { __ } from "../translation";

// panels: each panel's box height, in px.
defineProps<{
  sections: { title: string; rows?: number; panels?: number[] }[];
}>();

const BLOCK = "motion-reduce:animate-none";
</script>
