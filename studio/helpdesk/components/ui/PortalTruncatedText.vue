<template>
  <!-- An empty text keeps the trigger mounted but shows no bubble. -->
  <Tooltip :text="isTruncated ? text : ''">
    <span ref="textEl" v-bind="$attrs" class="truncate" @pointerenter="measure">
      {{ text }}
    </span>
  </Tooltip>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Tooltip } from "frappe-ui";

defineOptions({ inheritAttrs: false });
defineProps<{ text: string }>();

const textEl = ref<HTMLElement>();
const isTruncated = ref(false);

// On hover, so it follows resizes and text changes without an observer.
function measure() {
  isTruncated.value = textEl.value!.scrollWidth > textEl.value!.clientWidth;
}
</script>
