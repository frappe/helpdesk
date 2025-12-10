<template>
  <div
    class="flex flex-col p-4 bg-white border border-gray-200 rounded-lg cursor-pointer hover:shadow-md transition-shadow"
    @click="handleClick"
  >
    <span class="text-sm text-gray-500 font-medium">{{ label }}</span>
    <span class="text-2xl font-semibold mt-1" :style="{ color: displayColor }">
      {{ count }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

interface Props {
  label: string;
  count: number;
  color?: string;
  route?: string;
  filters?: Record<string, any>;
}

const props = withDefaults(defineProps<Props>(), {
  color: "#318AD8",
  route: "TicketsAgent",
  filters: () => ({}),
});

const router = useRouter();

const displayColor = computed(() => {
  if (props.count === 0) return "#A6B1B9";
  return props.color;
});

function handleClick() {
  if (props.route) {
    // Convert filter object to JSON string for query params
    const queryParams: Record<string, string> = {};
    if (Object.keys(props.filters).length > 0) {
      // Pass filters as JSON string to preserve complex filter structures
      queryParams.filters = JSON.stringify(props.filters);
    }
    
    router.push({
      name: props.route,
      query: queryParams,
    });
  }
}
</script>
