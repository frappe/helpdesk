<template>
  <div class="flex w-fit items-center">
    <Button
      :label="label"
      :class="count ? 'rounded-e-none' : ''"
      @click="$emit('toggle')"
    >
      <template #prefix><FilterIcon class="h-4" /></template>
      <template v-if="count" #suffix>
        <span
          class="flex h-5 w-5 items-center justify-center rounded-[5px] bg-surface-base pt-px text-xs-medium text-ink-gray-8 shadow-sm"
        >
          {{ count }}
        </span>
      </template>
    </Button>
    <Tooltip v-if="count" :text="__('Clear all Filter')">
      <div>
        <Button
          class="rounded-s-none border-s"
          icon="lucide-x"
          @click.stop="$emit('clear')"
        />
      </div>
    </Tooltip>
  </div>
</template>

<script setup lang="ts">
import FilterIcon from "@/components/icons/FilterIcon.vue";
import { __ } from "@/translation";
import { Button, Tooltip } from "frappe-ui";

interface P {
  count: number;
  label?: string;
}

interface E {
  (event: "toggle"): void;
  (event: "clear"): void;
}

withDefaults(defineProps<P>(), { label: "Filter" });
defineEmits<E>();
</script>
