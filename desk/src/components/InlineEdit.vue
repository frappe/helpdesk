<template>
  <div @click.stop="handleClick" class="inline-edit-wrapper">
    <div
      v-if="!editing"
      class="flex items-center gap-2 px-2 py-1 rounded cursor-pointer hover:bg-surface-gray-2 transition-colors group"
      :class="{ 'opacity-50': loading }"
    >
      <slot name="display" :value="modelValue">
        <span>{{ displayValue }}</span>
      </slot>
      <LucidePencil class="size-3 text-ink-gray-5 opacity-0 group-hover:opacity-100 transition-opacity" />
    </div>
    <Dropdown
      v-else
      :options="options"
      :modelValue="true"
      @update:modelValue="(val) => !val && (editing = false)"
      class="inline-edit-dropdown"
    >
      <template #default="{ open, close }">
        <div ref="dropdownRef" v-if="open" class="hidden"></div>
      </template>
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { Dropdown } from "frappe-ui";
import { computed, ref } from "vue";
import LucidePencil from "~icons/lucide/pencil";

interface Props {
  modelValue: string | null;
  options: Array<{ label: string; value: string; onClick?: () => void }>;
  displayValue?: string;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  displayValue: "",
  loading: false,
});

const emit = defineEmits(["update:modelValue", "change"]);

const editing = ref(false);
const dropdownRef = ref(null);

function handleClick(e: MouseEvent) {
  e.stopPropagation();
  e.preventDefault();
  editing.value = true;
}

// Enhance options with click handlers that emit change
const options = computed(() => {
  return props.options.map((opt) => ({
    ...opt,
    onClick: () => {
      emit("update:modelValue", opt.value);
      emit("change", opt.value);
      editing.value = false;
    },
  }));
});
</script>

<style scoped>
.inline-edit-wrapper {
  display: inline-block;
  min-width: 80px;
}
</style>

