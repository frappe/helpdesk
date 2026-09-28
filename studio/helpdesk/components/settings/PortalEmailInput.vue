<template>
  <div @keydown.capture="onKeydown">
    <MultiEmailInput
      v-model="emails"
      :options="options"
      :placeholder="placeholder"
      size="md"
      @update:query="query = $event"
    />
  </div>
</template>

<script setup lang="ts">
// `experimental/` is not in Studio's palette, so it reaches the block tree through this.
import { computed, ref } from "vue";
import { MultiEmailInput } from "frappe-ui/experimental";
import { validateEmail } from "@helpdesk/shared/utils";
import { matchesQuery } from "@app/utils";

const props = withDefaults(
  defineProps<{
    contacts?: { full_name: string; email: string; image?: string }[];
    placeholder?: string;
  }>(),
  { contacts: () => [], placeholder: "Add email…" }
);

const emails = defineModel<string[]>({ default: () => [] });

const query = ref("");

const options = computed(() =>
  props.contacts
    .filter((contact) =>
      matchesQuery(query.value, contact.full_name, contact.email)
    )
    .map((contact) => ({
      label: contact.full_name,
      value: contact.email,
      avatar: contact.image,
    }))
);

// It only splits on paste, but the placeholder promises commas.
function onKeydown(event: KeyboardEvent) {
  if (event.key !== "," && event.key !== ";") return;
  const input = event.target;
  if (!(input instanceof HTMLInputElement)) return;

  const email = input.value.trim().replace(/[,;]+$/, "");
  if (!email || !validateEmail(email)) return;
  event.preventDefault();

  if (
    !emails.value.some((entry) => entry.toLowerCase() === email.toLowerCase())
  ) {
    emails.value = [...emails.value, email];
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
