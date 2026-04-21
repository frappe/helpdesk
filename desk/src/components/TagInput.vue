<template>
  <div class="space-y-1.5">
    <FormLabel v-if="label" :label="label" />
    <div
      class="flex flex-col gap-1 w-full rounded px-2 py-1 border border-transparent"
      :class="[
        variant === 'ghost'
          ? 'bg-surface-white hover:bg-surface-white'
          : 'bg-surface-gray-2 hover:bg-surface-gray-3',
        inputClass,
        values.length && 'pl-1',
      ]"
      @click="inputRef?.focus()"
    >
      <div class="flex flex-wrap gap-1 min-h-7 items-center">
        <Pill
          ref="pillRefs"
          v-for="tag in values"
          :key="tag"
          :label="tag"
          @click="removeTag(tag)"
          @keydown.delete.capture.stop="removeFocusedPill(tag)"
        />
        <input
          ref="inputRef"
          v-model="query"
          autocomplete="off"
          class="flex-1 min-w-20 bg-transparent p-0 outline-none border-0 text-base text-ink-gray-8 h-7 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0 focus:border-0 ml-1"
          :placeholder="values?.length ? '' : placeholder"
          @keydown.enter.prevent="commit"
          @keydown.space.prevent="commit"
          @keydown.,.prevent="commit"
          @keydown.delete="removeLastTag"
          @blur="commit"
          @input="error = null"
          @paste.prevent="onPaste"
        />
      </div>
      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
    </div>
    <p v-if="description" class="text-xs text-ink-gray-5">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { FormLabel } from "frappe-ui";
import { computed, nextTick, ref } from "vue";
import Pill from "./Pill.vue";

const props = withDefaults(
  defineProps<{
    placeholder?: string;
    variant?: "subtle" | "ghost";
    inputClass?: string;
    validate?: ((value: string) => boolean) | null;
    label?: string;
    description?: string;
    errorMessage?: (input: string) => string;
  }>(),
  {
    placeholder: "",
    variant: "subtle",
    inputClass: "",
    validate: null,
    label: "",
    description: "",
    errorMessage: (input: string) => __(`"${input}" is not valid`),
  }
);

const values = defineModel<string[]>({ default: () => [] });
const query = ref("");

const pillRefs = ref<Array<{ rootRef: HTMLElement }>>([]);
const inputRef = ref<HTMLInputElement | null>(null);
const error = ref<string | null>(null);

function commit() {
  const tag = query.value.trim().replace(/,$/, "").trim();
  if (!tag) return;
  error.value = null;
  validateTag(tag);
  if (!values.value.includes(tag)) {
    values.value = [...values.value, tag];
  }
  query.value = "";
}
function validateTag(tag: string) {
  if (props.validate && !props.validate(tag)) {
    error.value = props.errorMessage(tag);
    throw new Error(error.value);
  }
}

function removeTag(tag: string) {
  values.value = values.value.filter((t) => t !== tag);
}

function removeLastTag(e: KeyboardEvent) {
  if (query.value) return;
  // First backspace: focus the last pill instead of deleting
  const lastPill = pillRefs.value[pillRefs.value.length - 1]?.rootRef;
  if (lastPill) {
    lastPill.focus();
  }
}

function removeFocusedPill(tag: string) {
  const idx = values.value.indexOf(tag);
  removeTag(tag);
  // After removal focus the previous pill, or the input if none left
  nextTick(() => {
    const prevPill = pillRefs.value[idx - 1]?.rootRef;
    if (prevPill) {
      prevPill.focus();
    } else {
      inputRef.value?.focus();
    }
  });
}

function onPaste(e: ClipboardEvent) {
  error.value = null;
  query.value = "";
  const text = e.clipboardData?.getData("text") ?? "";
  const parts = text
    .split(/[\s,]+/)
    .map((p) => p.trim())
    .filter(Boolean);
  const unique = new Set(parts.filter((p) => !values.value.includes(p)));
  if (unique.size) {
    unique.forEach((tag) => {
      validateTag(tag);
    });
    values.value = [...values.value, ...Array.from(unique)];
  }
  query.value = "";
}

function setFocus() {
  inputRef.value?.focus();
}

const hasError = computed(() => error.value !== null);

defineExpose({ setFocus, hasError });
</script>
