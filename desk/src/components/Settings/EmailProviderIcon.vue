<template>
  <div
    class="flex size-8 cursor-pointer items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200"
    :class="{ 'ring-2 ring-blue-500': selected }"
  >
    <img :src="logo" class="size-4.5" />
  </div>
  <p v-if="serviceName" class="text-center text-p-xs text-gray-700">
    {{ serviceName }}
  </p>
</template>

<script setup lang="ts">
interface P {
  serviceName?: string;
  logo?: string;
  selected?: boolean;
}

withDefaults(defineProps<P>(), {
  serviceName: "",
  selected: false,
  logo: "",
});
</script>

<style scoped></style>
