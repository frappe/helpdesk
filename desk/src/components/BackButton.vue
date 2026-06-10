<template>
  <Button
    variant="ghost"
    icon-left="lucide-chevron-left"
    :label="label"
    :size="size"
    class="!justify-start truncate font-medium text-ink-gray-8 hover:bg-transparent hover:opacity-70 focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 active:bg-transparent active:outline-none active:ring-0 rtl:flex-row-reverse"
    @click="$emit('back')"
  />
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";

interface P {
  label: string;
  size?: string;
}

interface E {
  (event: "back"): void;
}

withDefaults(defineProps<P>(), { size: "md" });
defineEmits<E>();
</script>
