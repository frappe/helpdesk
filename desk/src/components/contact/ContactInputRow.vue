<template>
  <div class="group relative w-full">
    <FormControl
      ref="control"
      class="[&_p]:text-p-xs"
      :type="type"
      :placeholder="placeholder"
      v-model="localValue"
      @blur="onBlur"
      @keydown.enter.prevent="commit"
      @keydown.escape="cancel"
    >
      <template #suffix>
        <div class="flex items-center gap-1">
          <Tooltip v-if="isPrimary" :text="__('Primary')">
            <span
              class="flex size-5 items-center justify-center rounded text-ink-amber-2"
              :aria-label="__('Primary')"
            >
              <LucideStar class="size-4 fill-ink-amber-2" />
            </span>
          </Tooltip>
          <Tooltip v-else :text="__('Set as primary')">
            <button
              type="button"
              class="invisible flex size-5 items-center justify-center rounded text-ink-gray-4 group-hover:visible focus-visible:visible hover:text-ink-amber-2"
              :aria-label="__('Set as primary')"
              @mousedown.prevent
              @click="$emit('setPrimary')"
            >
              <LucideStar class="size-4" />
            </button>
          </Tooltip>
          <Tooltip v-if="canRemove" :text="__('Remove')">
            <button
              type="button"
              class="flex size-5 items-center justify-center rounded text-ink-gray-4 hover:text-ink-red-3"
              :class="
                isPrimary
                  ? ''
                  : 'invisible group-hover:visible focus-visible:visible'
              "
              :aria-label="__('Remove')"
              @mousedown.prevent
              @click="$emit('remove')"
            >
              <LucideX class="size-3.5" />
            </button>
          </Tooltip>
        </div>
      </template>
    </FormControl>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { FormControl, Tooltip } from "frappe-ui";
import { nextTick, onMounted, ref, watch } from "vue";
import LucideStar from "~icons/lucide/star";
import LucideX from "~icons/lucide/x";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    isPrimary: boolean;
    canRemove: boolean;
    type?: "email" | "tel" | "text";
    placeholder?: string;
    autofocus?: boolean;
  }>(),
  {
    type: "text",
    placeholder: "",
    autofocus: false,
  }
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
  setPrimary: [];
  remove: [];
}>();

const localValue = ref(props.modelValue);
const control = ref<any>(null);

watch(
  () => props.modelValue,
  (v) => {
    if (document.activeElement !== getInputEl()) {
      localValue.value = v;
    }
  }
);

function getInputEl(): HTMLInputElement | null {
  return control.value?.$el?.querySelector?.("input") ?? null;
}

function onBlur() {
  if (localValue.value !== props.modelValue) {
    emit("update:modelValue", localValue.value);
  }
}

function commit() {
  getInputEl()?.blur();
}

function cancel() {
  localValue.value = props.modelValue;
  getInputEl()?.blur();
}

onMounted(() => {
  if (props.autofocus) {
    nextTick(() => getInputEl()?.focus());
  }
});
</script>
