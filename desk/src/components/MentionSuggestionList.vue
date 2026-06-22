<template>
  <div
    class="relative max-h-[300px] min-w-[220px] overflow-y-auto rounded-lg bg-white p-1 text-sm shadow-lg"
    @mouseleave="selectedItem = null"
  >
    <template v-for="(group, gi) in groupedItems" :key="gi">
      <div
        class="px-3 py-2 text-xs uppercase tracking-wide text-gray-500 bg-gray-50 select-none"
      >
        {{ group.label }}
      </div>
      <button
        v-for="(item, ii) in group.items"
        :key="ii"
        class="flex w-full items-center justify-start px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
        :class="{ 'bg-gray-100 text-gray-900': item === selectedItem }"
        @mouseover="selectedItem = item"
        @click.prevent="selectItem(item)"
      >
        {{ item.label }}
      </button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import type { MentionItem } from "@/tiptap-extensions";

const props = defineProps<{
  items: MentionItem[];
  command: (item: MentionItem) => void;
}>();

const selectedItem = ref<MentionItem | null>(null);

const groupedItems = computed(() => {
  const teams = props.items.filter((i) => i.group === "Teams");
  const agents = props.items.filter((i) => i.group === "Agents");
  const groups = [];
  if (teams.length) groups.push({ label: "Teams", items: teams });
  if (agents.length) groups.push({ label: "Agents", items: agents });
  return groups;
});

watch(
  () => props.items,
  () => {
    selectedItem.value = null;
  }
);

function selectItem(item: MentionItem) {
  props.command(item);
}

function onKeyDown({ event }: { event: KeyboardEvent }) {
  const flat = props.items;
  const idx = selectedItem.value ? flat.indexOf(selectedItem.value) : -1;
  if (event.key === "ArrowDown") {
    selectedItem.value = flat[Math.min(flat.length - 1, idx + 1)];
    return true;
  }
  if (event.key === "ArrowUp") {
    selectedItem.value = flat[Math.max(0, idx - 1)];
    return true;
  }
  if (event.key === "Enter") {
    if (selectedItem.value) selectItem(selectedItem.value);
    return true;
  }
  return false;
}

defineExpose({ onKeyDown });
</script>
