<template>
  <RadioGroup v-model="value">
    <div class="flex space-x-1 rounded bg-gray-100 p-0.5 text-sm">
      <RadioGroupOption
        v-for="button in buttons"
        :key="button.label"
        v-slot="{ active, checked }"
        as="template"
        :value="button.value ?? button.label"
      >
        <button
          :class="[
            active ? 'ring-gray-300 focus-visible:ring' : '',
            checked ? 'bg-white text-gray-900 shadow' : 'text-gray-700',
            'rounded-[7px] px-2 py-1.5 leading-none transition-colors focus:outline-none',
          ]"
        >
          <RadioGroupLabel as="span">{{ button.label }}</RadioGroupLabel>
        </button>
      </RadioGroupOption>
    </div>
  </RadioGroup>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RadioGroup, RadioGroupOption, RadioGroupLabel } from "@headlessui/vue";

type ModelValue = string | boolean | number;

interface Button {
  label: string;
  value?: ModelValue;
}

interface P {
  buttons: Button[];
  modelValue: ModelValue;
}

interface E {
  (event: "update:modelValue", value: ModelValue): void;
}

const props = defineProps<P>();
const emit = defineEmits<E>();

const value = computed({
  get() {
    return props.modelValue;
  },
  set(v) {
    emit("update:modelValue", v);
  },
});
</script>
