<template>
  <Popover v-model:open="isOpen" @close="handlePopoverToggle">
    <template #target="{ togglePopover }">
      <div
        @click="!disabled && togglePopover()"
        class="min-h-7 w-full cursor-pointer select-none leading-5 p-1 px-2 rounded"
      >
        <div class="flex items-center justify-between">
          <span :class="{ 'text-gray-600': !modelValue || disabled }">
            {{ formattedValue }}
          </span>
        </div>
      </div>
    </template>

    <template #body="{ close }">
      <div class="absolute bg-white top-2">
        <!-- Built-in Duration Picker -->
        <div
          class="flex gap-2 border border-gray-300 rounded w-fit min-w-max px-4 select-none shadow-sm"
        >
          <!-- Hours -->
          <div
            v-if="showHours"
            class="p-2 flex flex-col items-center group relative"
          >
            <div class="flex items-center gap-1">
              <input
                ref="hoursInput"
                v-model.number="hoursValue"
                type="number"
                min="0"
                max="23"
                class="w-8 text-sm bg-transparent border-0 p-0 text-center focus:ring-0 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                @keyup.enter="$event.target.blur()"
              />
              <div
                class="flex flex-col group-hover:opacity-100 opacity-0 absolute top-1/2 -translate-y-1/2 -right-3"
              >
                <button
                  @click="increment('hours')"
                  class="hover:bg-gray-100 rounded-sm select-none px-1 py-0.5 text-xs"
                >
                  <FeatherIcon name="chevron-up" class="size-3.5" />
                </button>
                <button
                  @click="decrement('hours')"
                  class="hover:bg-gray-100 rounded-sm select-none px-1 py-0.5 text-xs"
                >
                  <FeatherIcon name="chevron-down" class="size-3.5" />
                </button>
              </div>
            </div>
            <div class="text-xs text-gray-600 mt-1">Hrs</div>
          </div>

          <!-- Minutes -->
          <div
            v-if="showMinutes"
            class="p-2 flex flex-col items-center group relative"
          >
            <div class="flex items-center gap-1">
              <input
                ref="minutesInput"
                v-model.number="minutesValue"
                type="number"
                min="0"
                max="59"
                class="w-8 text-sm bg-transparent border-0 p-0 text-center focus:ring-0 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                @keyup.enter="$event.target.blur()"
              />
              <div
                class="flex flex-col group-hover:opacity-100 opacity-0 absolute top-1/2 -translate-y-1/2 -right-3"
              >
                <button
                  @click="increment('minutes')"
                  class="hover:bg-gray-100 rounded-sm select-none px-1 py-0.5 text-xs"
                >
                  <FeatherIcon name="chevron-up" class="size-3.5" />
                </button>
                <button
                  @click="decrement('minutes')"
                  class="hover:bg-gray-100 rounded-sm select-none px-1 py-0.5 text-xs"
                >
                  <FeatherIcon name="chevron-down" class="size-3.5" />
                </button>
              </div>
            </div>
            <div class="text-xs text-gray-600 mt-1">Min</div>
          </div>

          <!-- Seconds -->
          <div
            v-if="showSeconds"
            class="p-2 flex flex-col items-center group relative"
          >
            <div class="flex items-center gap-1">
              <input
                ref="secondsInput"
                v-model.number="secondsValue"
                type="number"
                min="0"
                max="59"
                class="w-8 text-sm bg-transparent border-0 p-0 text-center focus:ring-0 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
              <div
                class="flex flex-col group-hover:opacity-100 opacity-0 absolute top-1/2 -translate-y-1/2 -right-3"
              >
                <button
                  @click="increment('seconds')"
                  class="hover:bg-gray-100 rounded-sm select-none px-1 py-0.5 text-xs"
                >
                  <FeatherIcon name="chevron-up" class="size-3.5" />
                </button>
                <button
                  @click="decrement('seconds')"
                  class="hover:bg-gray-100 rounded-sm select-none px-1 py-0.5 text-xs"
                >
                  <FeatherIcon name="chevron-down" class="size-3.5" />
                </button>
              </div>
            </div>
            <div class="text-xs text-gray-600 mt-1">Sec</div>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { Popover } from "frappe-ui";
import { computed, ref, watch } from "vue";

const props = defineProps({
  modelValue: {
    type: Number,
    default: 0,
  },
  placeholder: {
    type: String,
    default: "Set duration",
  },
  showHours: {
    type: Boolean,
    default: true,
  },
  showMinutes: {
    type: Boolean,
    default: true,
  },
  showSeconds: {
    type: Boolean,
    default: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:modelValue"]);

const isOpen = ref(false);
const hoursValue = ref(0);
const minutesValue = ref(0);
const secondsValue = ref(0);

// Convert modelValue to hours, minutes, seconds
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      hoursValue.value = Math.floor(newValue / 3600);
      minutesValue.value = Math.floor((newValue % 3600) / 60);
      secondsValue.value = newValue % 60;
    } else {
      hoursValue.value = 0;
      minutesValue.value = 0;
      secondsValue.value = 0;
    }
  },
  { immediate: true }
);

const formattedValue = computed(() => {
  const hrs = hoursValue.value;
  const mins = minutesValue.value;
  return `${hrs} hours ${mins} minutes`;
});

// Handle popover open/close
const handlePopoverToggle = (open) => {
  if (!open) {
    // Popover is closing, update the model value
    validateAndUpdate();
  }
};

const validateAndUpdate = () => {
  // Ensure values are within bounds
  hoursValue.value = Math.max(0, hoursValue.value || 0);
  minutesValue.value = Math.max(0, Math.min(59, minutesValue.value || 0));
  secondsValue.value = Math.max(0, Math.min(59, secondsValue.value || 0));

  // Convert to total seconds and emit
  const totalSeconds =
    hoursValue.value * 3600 + minutesValue.value * 60 + secondsValue.value;
  emit("update:modelValue", totalSeconds);
};

const increment = (unit) => {
  if (unit === "hours") {
    hoursValue.value = (hoursValue.value || 0) + 1;
  } else if (unit === "minutes") {
    minutesValue.value = Math.min(59, (minutesValue.value || 0) + 1);
  } else if (unit === "seconds") {
    secondsValue.value = Math.min(59, (secondsValue.value || 0) + 1);
  }
  // Don't call validateAndUpdate here
};

const decrement = (unit) => {
  if (unit === "hours") {
    hoursValue.value = Math.max(0, (hoursValue.value || 0) - 1);
  } else if (unit === "minutes") {
    minutesValue.value = Math.max(0, (minutesValue.value || 0) - 1);
  } else if (unit === "seconds") {
    secondsValue.value = Math.max(0, (secondsValue.value || 0) - 1);
  }
};
</script>
