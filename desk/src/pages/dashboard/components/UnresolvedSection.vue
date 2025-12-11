<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h3 class="text-base font-medium text-gray-900">Unresolved tickets</h3>
        <p class="text-xs text-gray-500">Across helpdesk</p>
      </div>
      <button
        class="text-sm text-blue-600 hover:text-blue-700"
        @click="handleViewDetails"
      >
        View details
      </button>
    </div>

    <div v-if="groups.length > 0">
      <div class="grid grid-cols-2 gap-2 text-sm text-gray-500 mb-2">
        <span>Group</span>
        <span class="text-right">Open</span>
      </div>
      <div
        v-for="group in groups"
        :key="group.name"
        class="grid grid-cols-2 gap-2 py-2 border-t border-gray-100"
      >
        <span class="text-sm text-gray-700">{{ group.name || "Unassigned" }}</span>
        <span class="text-sm text-gray-900 font-medium text-right">{{ group.count }}</span>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-8 text-gray-400">
      <LucideCheckCircle class="w-8 h-8 mb-2" />
      <span class="text-sm">All caught up! No unresolved tickets</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import LucideCheckCircle from "~icons/lucide/check-circle";

interface UnresolvedGroup {
  name: string;
  count: number;
}

interface Props {
  groups: UnresolvedGroup[];
}

defineProps<Props>();

const router = useRouter();

function handleViewDetails() {
  router.push({
    name: "TicketsAgent",
    query: { status: "Open" },
  });
}
</script>
