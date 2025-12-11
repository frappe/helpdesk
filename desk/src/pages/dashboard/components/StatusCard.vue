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
  team?: string | null;
  agent?: string | null;
}

const props = withDefaults(defineProps<Props>(), {
  color: "#318AD8",
  route: "TicketsAgent",
  filters: () => ({}),
  team: null,
  agent: null,
});

const router = useRouter();

const displayColor = computed(() => {
  if (props.count === 0) return "#A6B1B9";
  return props.color;
});

function handleClick() {
  if (props.route) {
    // Merge status filters with team/agent filters
    const combinedFilters: Record<string, any> = { ...props.filters };
    
    // Add team filter if selected
    if (props.team) {
      combinedFilters.agent_group = props.team;
    }
    
    // Add agent filter if selected
    if (props.agent) {
      combinedFilters._assign = ["LIKE", `%${props.agent}%`];
    }
    
    // Convert filter object to JSON string for query params
    const queryParams: Record<string, string> = {};
    if (Object.keys(combinedFilters).length > 0) {
      // Pass filters as JSON string to preserve complex filter structures
      queryParams.filters = JSON.stringify(combinedFilters);
    }
    
    router.push({
      name: props.route,
      query: queryParams,
    });
  }
}
</script>
