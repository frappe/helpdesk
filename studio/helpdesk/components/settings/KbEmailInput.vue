<template>
  <div ref="root" @keydown.capture="onKeydown">
    <MultiEmailInput
      :modelValue="modelValue"
      :options="options"
      :placeholder="placeholder"
      size="md"
      @update:modelValue="$emit('update:modelValue', $event)"
      @update:query="query = $event"
    />
  </div>
</template>

<script setup lang="ts">
// `experimental/` is not in Studio's palette, so it reaches the block tree through this.
import { validateEmail } from "@helpdesk/shared/utils";
import { MultiEmailInput } from "frappe-ui/experimental";
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue?: string[];
    // People who may be invited, offered as suggestions while typing.
    contacts?: {
      contact: string;
      full_name: string;
      email: string;
      image?: string;
    }[];
    placeholder?: string;
  }>(),
  { modelValue: () => [], contacts: () => [], placeholder: "Add email…" }
);

const emit = defineEmits<{ "update:modelValue": [value: string[]] }>();

const root = ref<HTMLElement | null>(null);
const query = ref("");

// MultiEmailInput drops only what is already selected, leaving the matching to its host.
const options = computed(() => {
  const needle = query.value.trim().toLowerCase();
  return props.contacts
    .filter(
      (contact) =>
        !needle ||
        `${contact.full_name} ${contact.email}`.toLowerCase().includes(needle)
    )
    .map((contact) => ({
      label: contact.full_name,
      value: contact.email,
      avatar: contact.image,
    }));
});

// It only splits on paste, but the placeholder promises commas.
function onKeydown(event: KeyboardEvent) {
  if (event.key !== "," && event.key !== ";") return;
  const input = event.target;
  if (!(input instanceof HTMLInputElement)) return;

  const email = input.value.trim().replace(/[,;]+$/, "");
  if (!email || !validateEmail(email)) return;
  event.preventDefault();

  if (
    !props.modelValue.some(
      (entry) => entry.toLowerCase() === email.toLowerCase()
    )
  ) {
    emit("update:modelValue", [...props.modelValue, email]);
  }
  clear(input);
}

// v-model, so only the native setter plus an input event is noticed.
function clear(input: HTMLInputElement) {
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value"
  )?.set;
  setter?.call(input, "");
  input.dispatchEvent(new Event("input", { bubbles: true }));
}
</script>
