<template>
  <MultiEmailInput
    v-model="emails"
    :options="options"
    :placeholder="placeholder"
    size="md"
    @update:query="query = $event"
  />
</template>

<script setup lang="ts">
// `experimental/` isn't in Studio's palette.
import { computed, ref, watch } from "vue";
import { debounce } from "frappe-ui";
import { MultiEmailInput } from "frappe-ui/experimental";
import { SEARCH_DEBOUNCE_MS } from "@helpdesk/shared/utils";

type Contact = { full_name: string; email: string; image?: string };

const props = defineProps<{
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
    // Drop stale answers.
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
</script>
