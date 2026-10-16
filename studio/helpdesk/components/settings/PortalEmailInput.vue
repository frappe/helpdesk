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
import { computed, ref, watch } from "vue";
import { debounce } from "frappe-ui";
import { isValidEmail, MultiEmailInput } from "frappe-ui/experimental";
import { SEARCH_DEBOUNCE_MS } from "@helpdesk/shared/utils";

type Contact = { full_name: string; email: string; image?: string };

const props = defineProps<{
  // Matched on the server: there are too many contacts to send them all.
  searchContacts?: (query: string) => Promise<Contact[]>;
  placeholder?: string;
}>();

const emails = defineModel<string[]>({ default: () => [] });

const query = ref("");
const contacts = ref<Contact[]>([]);

const search = debounce(async () => {
  const asked = query.value;
  try {
    const found = (await props.searchContacts?.(asked)) || [];
    // A slower, older answer must not replace a newer one.
    if (asked === query.value) contacts.value = found;
  } catch (error) {
    console.error(error);
  }
}, SEARCH_DEBOUNCE_MS);
watch(query, search, { immediate: true });

const options = computed(() =>
  contacts.value.map((contact) => ({
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
  if (!email || !isValidEmail(email)) return;
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
