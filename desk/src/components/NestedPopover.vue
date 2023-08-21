<template>
  <Popover v-slot="{ open }">
    <PopoverButton
      ref="reference"
      v-slot="{ open }"
      as="div"
      @click="updatePosition"
      @focusin="updatePosition"
      @keydown="updatePosition"
    >
      <slot name="target" v-bind="{ open }" />
    </PopoverButton>
    <div v-show="open">
      <PopoverPanel
        v-slot="{ open, close }"
        ref="popover"
        static
        class="z-[100]"
      >
        <slot name="body" v-bind="{ open, close }" />
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
