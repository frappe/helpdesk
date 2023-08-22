<template>
  <Popover v-slot="{ open }">
    <PopoverButton
      ref="reference"
      v-slot="{ open: o }"
      as="div"
      @click="updatePosition"
      @focusin="updatePosition"
      @keydown="updatePosition"
    >
      <slot name="target" :open="o" />
    </PopoverButton>
    <div v-show="open">
      <PopoverPanel
        v-slot="{ open: o, close }"
        ref="popover"
        static
        class="z-[100]"
      >
        <slot name="body" :open="o" :close="close" />
      </PopoverPanel>
    </div>
  </Popover>
</template>

<script setup>
import { nextTick, ref, onBeforeUnmount } from "vue";
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue";
import { createPopper } from "@popperjs/core";

const props = defineProps({
  placement: {
    type: String,
    default: "bottom-start",
  },
});

const reference = ref(null);
const popover = ref(null);

let popper = ref(null);

function setupPopper() {
  if (!popper.value) {
    popper.value = createPopper(reference.value.el, popover.value.el, {
      placement: props.placement,
    });
  } else {
    popper.value.update();
  }
}

function updatePosition() {
  nextTick(() => setupPopper());
}

onBeforeUnmount(() => {
  popper.value?.destroy();
});
</script>
