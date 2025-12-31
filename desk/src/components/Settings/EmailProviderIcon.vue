<template>
  <div
    class="flex size-8 cursor-pointer items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200"
    :class="{ 'ring-2 ring-blue-500': selected }"
  >
    <img v-if="logoValue" :src="logoValue" class="size-4.5" />
    <LucideMail v-else class="size-4.5 text-gray-700" />
  </div>
  <p v-if="serviceName" class="text-center text-p-xs text-gray-700">
    {{ serviceName }}
  </p>
</template>

<script setup lang="ts">
import { computed } from "vue";
import LucideMail from "~icons/lucide/mail";

interface P {
  serviceName?: string;
  logo?: string;
  selected?: boolean;
}

const props = withDefaults(defineProps<P>(), {
  serviceName: "",
  selected: false,
  logo: "",
});

const logoValue = computed(() => props.logo);
</script>

<style scoped></style>
