<template>
  <!-- DaisyUI Dropdown-based Popover -->
  <div class="relative">
    <div
      ref="reference"
      @click="toggleOpen"
      @focusin="updatePosition"
      @keydown="updatePosition"
    >
      <slot name="target" :open="open" />
    </div>
    <div v-show="open">
      <div
        ref="popover"
        class="z-[100]"
      >
        <slot name="body" :open="open" :close="close" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, onBeforeUnmount, onMounted } from "vue";
import { createPopper } from "@popperjs/core";

const props = defineProps({
  placement: {
    type: String,
    default: "bottom-start",
  },
});

const reference = ref(null);
const popover = ref(null);
const open = ref(false);

let popper = ref(null);

function setupPopper() {
  if (!popper.value && reference.value && popover.value) {
    popper.value = createPopper(reference.value, popover.value, {
      placement: props.placement,
    });
  } else if (popper.value) {
    popper.value.update();
  }
}

function updatePosition() {
  if (open.value) {
    nextTick(() => setupPopper());
  }
}

function toggleOpen() {
  open.value = !open.value;
  updatePosition();
}

function close() {
  open.value = false;
}

// Close on click outside
function handleClickOutside(event) {
  if (
    reference.value &&
    popover.value &&
    !reference.value.contains(event.target) &&
    !popover.value.contains(event.target)
  ) {
    close();
  }
}

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleClickOutside);
  popper.value?.destroy();
});
</script>
