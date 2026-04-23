<template>
  <div
    class="flex size-8 cursor-pointer items-center justify-center rounded-full bg-surface-gray-2 hover:bg-surface-gray-3"
    :class="{ 'ring-2 ring-blue-500': selected }"
  >
    <img v-if="logoValue" :src="logoValue" class="size-4.5" />
    <LucideMail v-else class="size-4.5 text-ink-gray-7" />
  </div>
  <p v-if="serviceName" class="text-center text-p-xs text-ink-gray-7">
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
