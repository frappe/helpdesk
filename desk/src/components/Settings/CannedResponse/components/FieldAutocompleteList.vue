<template>
  <div
    v-if="props.items.length > 0"
    class="max-h-[300px] min-w-40 overflow-y-auto rounded-lg bg-surface-white p-1 text-base shadow-lg pointer-events-auto hide-scrollbar"
  >
    <button
      v-for="(item, index) in props.items"
      :key="item.value"
      :ref="
        (el) => {
          if (el) itemRefs[index] = el as HTMLButtonElement
        }
      "
      :class="[
        'flex w-full items-center whitespace-nowrap rounded-md px-2 py-1.5 text-sm text-ink-gray-9',
        index === selectedIndex ? 'bg-surface-gray-2' : '',
      ]"
      @click="selectItem(index)"
      @mouseover="selectedIndex = index"
    >
      {{ item.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUpdate, ref, watch, type PropType } from "vue";
import type { Editor, Range } from "@tiptap/core";
import { FieldItem } from "../../../../tiptap-extensions";

const props = defineProps({
  items: {
    type: Array as PropType<any[]>,
    required: true,
  },
  editor: {
    type: Object as PropType<Editor>,
    required: true,
  },
  range: {
    type: Object as PropType<Range>,
    required: true,
  },
  command: {
    type: Function as PropType<(item: FieldItem) => void>,
    required: true,
  },
  query: String,
});

const selectItem = (index: number) => {
  const item = props.items[index];
  if (item) {
    props.command(item);
  }
};

const onKeyDown = ({ event }: { event: KeyboardEvent }) => {
  if (!props.items.length) return false;

  if (event.key === "ArrowUp") {
    upHandler();
    return true;
  }
  if (event.key === "ArrowDown") {
    downHandler();
    return true;
  }
  if (event.key === "Enter") {
    enterHandler();
    return true;
  }
  return false;
};
const selectedIndex = ref(0);
const itemRefs = ref<HTMLButtonElement[]>([]);

onBeforeUpdate(() => {
  itemRefs.value = [];
});

const scrollIntoView = () => {
  nextTick(() => {
    const selectedElement = itemRefs.value[selectedIndex.value];
    if (selectedElement) {
      selectedElement.scrollIntoView({ block: "nearest" });
    }
  });
};

const upHandler = () => {
  selectedIndex.value =
    (selectedIndex.value + props.items.length - 1) % props.items.length;
  scrollIntoView();
};

const downHandler = () => {
  selectedIndex.value = (selectedIndex.value + 1) % props.items.length;
  scrollIntoView();
};

const enterHandler = () => {
  selectItem(selectedIndex.value);
};

defineExpose({
  onKeyDown,
});

watch(
  () => props.items,
  () => {
    selectedIndex.value = 0;
  }
);
</script>
