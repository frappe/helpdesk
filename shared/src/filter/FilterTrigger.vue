<template>
  <div class="flex w-fit items-center">
    <Button
      :label="label"
      :class="count ? 'rounded-e-none' : ''"
      @click="$emit('toggle')"
    >
      <template #prefix><FilterIcon class="h-4" /></template>
      <template #suffix>
        <!-- -ms-2 cancels the Button's gap while the badge is closed -->
        <span
          :class="[REVEAL, count ? 'grid-cols-[1fr]' : '-ms-2 grid-cols-[0fr]']"
          :aria-hidden="!count"
        >
          <span class="min-w-0 overflow-hidden">
            <span
              class="flex h-5 w-5 items-center justify-center rounded-[5px] bg-surface-base pt-px text-xs-medium text-ink-gray-8 shadow-sm"
            >
              {{ count || "" }}
            </span>
          </span>
        </span>
      </template>
    </Button>
    <!-- invisible: a collapsed X still has a box; visibility waits out the transition -->
    <div
      :class="[REVEAL, count ? 'grid-cols-[1fr]' : 'invisible grid-cols-[0fr]']"
      :inert="!count"
    >
      <div class="min-w-0 overflow-hidden">
        <Tooltip :text="__('Clear all Filter')">
          <div>
            <Button
              class="rounded-s-none border-s"
              icon="lucide-x"
              :aria-label="__('Clear all Filter')"
              @click.stop="$emit('clear')"
            />
          </div>
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import FilterIcon from "../FilterIcon.vue";
import { __ } from "../translation";
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

// A 0fr to 1fr grid column animates the width, which `auto` cannot.
const REVEAL =
  "grid transition-all duration-200 ease-out motion-reduce:transition-none";
defineEmits<E>();
</script>
