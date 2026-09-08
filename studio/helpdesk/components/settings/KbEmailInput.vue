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
// frappe-ui ships MultiEmailInput under `experimental/`, which isn't in Studio's
// component palette, so it reaches the block tree through this wrapper. The
// package only exports the barrel — deep paths aren't in its export map.
import { MultiEmailInput } from "frappe-ui/experimental";
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    /** The addresses entered so far. */
    modelValue?: string[];
    /** People who may be invited, offered as suggestions while typing. */
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

// MultiEmailInput leaves the matching to its host and only drops what is already
// selected, so an unfiltered list would offer every colleague on every keystroke.
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

// MultiEmailInput only splits on paste; Enter commits one address at a time. The
// placeholder promises commas, so commit the typed address on one here too.
function onKeydown(event: KeyboardEvent) {
  if (event.key !== "," && event.key !== ";") return;
  const input = event.target;
  if (!(input instanceof HTMLInputElement)) return;

  const email = input.value.trim().replace(/[,;]+$/, "");
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return;
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

// The control drives its query with v-model, so the native setter plus an input
// event is what makes it notice the field is empty again.
function clear(input: HTMLInputElement) {
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value"
  )?.set;
  setter?.call(input, "");
  input.dispatchEvent(new Event("input", { bubbles: true }));
}
</script>
