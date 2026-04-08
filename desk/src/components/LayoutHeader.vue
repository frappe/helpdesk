<template>
  <Teleport to="#app-header" v-if="showHeader">
    <slot>
      <header
        class="flex h-10.5 items-center justify-between mx-4 md:mx-5 md:mr-0"
      >
        <div class="flex items-center gap-2 max-w-[70%] md:max-w-[50%]">
          <slot name="left-header" />
        </div>
        <div class="flex items-center gap-2">
          <slot name="right-header" class="flex items-center gap-2" />
        </div>
      </header>
    </slot>
  </Teleport>
</template>
<script setup>
import { nextTick, ref } from "vue";
const showHeader = ref(false);

nextTick(() => {
  showHeader.value = true;
});
</script>
