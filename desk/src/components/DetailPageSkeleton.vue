<template>
  <div class="flex h-full flex-col gap-5" aria-hidden="true">
    <div class="flex items-center justify-between px-5 pt-5">
      <div class="flex items-center gap-4">
        <Skeleton
          variant="box"
          class="h-12 w-12"
          :class="avatarShape === 'circle' && 'rounded-full'"
        />
        <div class="space-y-2">
          <Skeleton class="h-4 w-40" />
          <Skeleton class="h-3 w-64" />
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Skeleton variant="box" class="h-7 w-16" />
        <Skeleton variant="box" class="h-7 w-7" />
      </div>
    </div>
    <div class="grid grid-cols-4 gap-2.5 px-5">
      <div
        v-for="card in 4"
        :key="card"
        class="flex min-h-[120px] flex-col justify-between rounded-md border p-4"
      >
        <Skeleton class="h-4 w-1/2" />
        <Skeleton variant="box" class="h-7 w-12" />
        <Skeleton class="h-3 w-1/3" />
      </div>
    </div>
    <div class="flex gap-6 border-b px-5 pb-2">
      <Skeleton v-for="tab in 2" :key="tab" class="h-3.5 w-20" />
    </div>
    <div class="space-y-4 px-5">
      <Skeleton
        v-for="row in 6"
        :key="row"
        class="h-3.5"
        :class="row % 2 ? 'w-full' : 'w-5/6'"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Skeleton } from "./Skeleton";

interface Props {
  avatarShape?: "circle" | "square";
}

withDefaults(defineProps<Props>(), { avatarShape: "circle" });
</script>
