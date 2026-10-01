<template>
  <div class="flex flex-col">
    <div class="px-2 pt-2">
      <TextInput
        ref="searchInput"
        v-model="query"
        type="text"
        :placeholder="placeholder"
        autocomplete="off"
        @keydown="onKeydown"
        variant="outline"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-5" />
        </template>
        <template #suffix>
          <kbd
            v-if="showShortcutHint && !query"
            class="flex h-5 w-5 items-center justify-center rounded-[5px] border border-outline-gray-2 bg-surface-base pt-px text-xs text-ink-gray-5"
          >
            F
          </kbd>
        </template>
      </TextInput>
    </div>
    <div
      ref="listEl"
      role="listbox"
      :aria-label="__('Fields')"
      class="mt-1 max-h-64 overflow-y-auto p-1"
    >
      <button
        v-for="(field, index) in filteredFields"
        :key="field.fieldname"
        :data-index="index"
        role="option"
        :aria-selected="index === activeIndex"
        :class="[
          'flex h-8 w-full items-center gap-2 rounded px-2 text-base text-ink-gray-8',
          index === activeIndex ? 'bg-surface-gray-2' : '',
        ]"
        @mousemove="activeIndex = index"
        @click="$emit('select', field)"
      >
        <component :is="fieldIcon(field)" class="size-4 text-ink-gray-5" />
        <span :title="field.label" class="flex-1 truncate text-start">{{
          field.label
        }}</span>
        <LucideChevronRight class="size-4 text-ink-gray-4" />
      </button>
      <div
        v-if="!filteredFields.length"
        class="flex h-8 items-center px-2 text-base text-ink-gray-5"
      >
        {{ __("No fields found") }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { TextInput } from "frappe-ui";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { fieldIcon, FilterField } from "./filter";

interface P {
  fields: FilterField[];
  placeholder?: string;
  showShortcutHint?: boolean;
}

interface E {
  (event: "select", field: FilterField): void;
  (event: "back"): void;
}

const props = withDefaults(defineProps<P>(), {
  placeholder: "Search fields...",
  showShortcutHint: false,
});
const emit = defineEmits<E>();

const query = ref("");
const activeIndex = ref(0);
const searchInput = ref(null);
const listEl = ref<HTMLElement | null>(null);

const filteredFields = computed(() => {
  if (!query.value) return props.fields;
  return props.fields.filter((f) =>
    f.label.toLowerCase().includes(query.value.toLowerCase())
  );
});

function onKeydown(event: KeyboardEvent) {
  if (event.isComposing) return;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    event.stopPropagation();
    const delta = event.key === "ArrowDown" ? 1 : -1;
    const total = filteredFields.value.length;
    if (total) activeIndex.value = (activeIndex.value + delta + total) % total;
  } else if (event.key === "Enter") {
    event.preventDefault();
    event.stopPropagation();
    if (event.repeat) return;
    const field = filteredFields.value[activeIndex.value];
    if (field) emit("select", field);
  } else if (event.key === "Backspace" && !query.value) {
    event.stopPropagation();
    emit("back");
  }
}

watch(query, () => (activeIndex.value = 0));

watch(activeIndex, (index) => {
  nextTick(() => {
    listEl.value
      ?.querySelector(`[data-index="${index}"]`)
      ?.scrollIntoView({ block: "nearest" });
  });
});

onMounted(() => {
  // preventScroll: the panel mounts mid-swipe, still translated; a default
  // focus would scroll it into view and visually cancel the slide
  nextTick(() => searchInput.value?.el?.focus({ preventScroll: true }));
});
</script>
