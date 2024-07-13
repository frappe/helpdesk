<template>
  <header class="flex h-12 items-center justify-between border-b py-2.5 pl-5">
    <div class="left-header flex max-w-[70%] items-center gap-2">
      <slot name="left-header" />
    </div>
    <div class="flex items-center gap-2 px-5">
      <slot name="right-header" class="flex items-center gap-2" />
    </div>
  </header>
</template>

<script setup>
import { onMounted } from "vue";

onMounted(() => {
  const leftHeader = document.querySelector(".left-header");

  const currentRoute = leftHeader.querySelector('[aria-current="page"]');
  currentRoute.classList.add("truncate");

  const span = currentRoute.querySelector("span");
  span.classList.add("truncate");
});
</script>
