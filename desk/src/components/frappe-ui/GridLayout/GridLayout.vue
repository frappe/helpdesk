<template>
  <GridLayout
    v-model:layout="layout"
    v-bind="options"
    @layout-ready="() => (layoutReady = true)"
  >
    <GridItem
      v-for="(l, index) in layout"
      :key="l.i"
      :i="l.i"
      :x="l.x"
      :y="l.y"
      :w="l.w"
      :h="l.h"
      :min-w="l.minW"
      :min-h="l.minH"
      :max-w="l.maxW"
      :max-h="l.maxH"
    >
      <slot
        v-if="layoutReady"
        name="item"
        :index="index"
        :i="l.i"
        :x="l.x"
        :y="l.y"
        :w="l.w"
        :h="l.h"
        :min-w="l.minW"
        :min-h="l.minH"
        :max-w="l.maxW"
        :max-h="l.maxH"
      >
        <pre class="h-full w-full rounded bg-surface-base p-4 shadow">{{
          {
            i: l.i,
            x: l.x,
            y: l.y,
            w: l.w,
            h: l.h,
            minW: l.minW,
            minH: l.minH,
            maxW: l.maxW,
            maxH: l.maxH,
          }
        }}</pre>
      </slot>
    </GridItem>
  </GridLayout>
</template>

<script setup lang="ts">
import { GridLayout, GridItem } from "grid-layout-plus";
import { Layout, GridLayoutProps } from "./types";
import { computed, reactive, ref } from "vue";

const props = defineProps<GridLayoutProps>();

const layout = defineModel<Layout>({
  type: Array as () => Layout,
  default: () => [],
});

const layoutReady = ref(false);

const options = reactive({
  colNum: props.cols || 12,
  margin: [0, 0],
  rowHeight: props.rowHeight || 52,
  isDraggable: computed(() => !props.disabled),
  isResizable: computed(() => !props.disabled),
  responsive: true,
  verticalCompact: true,
  preventCollision: false,
  useCssTransforms: true,
  cols: {
    lg: props.cols || 12,
    md: props.cols || 12,
    sm: props.cols || 12,
    xs: 1,
    xxs: 1,
  },
});
</script>

<style scoped>
.vgl-layout {
  --vgl-placeholder-bg: #b1b1b1;
  --vgl-placeholder-opacity: 15%;
  --vgl-placeholder-z-index: 2;

  --vgl-item-resizing-z-index: 3;
  --vgl-item-resizing-opacity: 100%;
  --vgl-item-dragging-z-index: 3;
  --vgl-item-dragging-opacity: 100%;

  --vgl-resizer-size: 10px;
  --vgl-resizer-border-color: #444;
  --vgl-resizer-border-width: 2px;
}

:deep(.vgl-item--placeholder) {
  z-index: var(--vgl-placeholder-z-index, 2);
  user-select: none;
  background-color: var(--vgl-placeholder-bg);
  opacity: var(--vgl-placeholder-opacity);
  transition-duration: 100ms;
  border-radius: 0.5rem;
}

:deep(.vgl-item__resizer) {
  position: absolute;
  right: 12px;
  bottom: 12px;
  box-sizing: border-box;
  width: var(--vgl-resizer-size);
  height: var(--vgl-resizer-size);
  cursor: se-resize;
}

:deep(.vgl-item__resizer:before) {
  position: absolute;
  inset: 0 3px 3px 0;
  content: "";
  border: 0 solid var(--vgl-resizer-border-color);
  border-right-width: var(--vgl-resizer-border-width);
  border-bottom-width: var(--vgl-resizer-border-width);
}
</style>
