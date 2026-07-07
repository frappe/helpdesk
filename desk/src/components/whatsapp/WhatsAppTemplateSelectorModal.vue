<template>
  <Dialog v-model:open="show" :options="{ title: __('WhatsApp Templates') }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <TextInput
          v-model="search"
          type="text"
          :placeholder="__('Search templates')"
          :debounce="300"
        >
          <template #prefix>
            <FeatherIcon name="search" class="size-4 text-ink-gray-5" />
          </template>
        </TextInput>

        <div class="flex max-h-[50vh] flex-col gap-2 overflow-y-auto">
          <button
            v-for="template in filteredTemplates"
            :key="template.name"
            class="rounded-md border border-outline-gray-2 p-3 text-left transition hover:border-outline-gray-3 hover:bg-surface-gray-1"
            @click="emit('send', template.name)"
          >
            <div class="mb-1 font-medium text-ink-gray-8">
              {{ template.name }}
            </div>
            <div class="line-clamp-3 text-p-sm text-ink-gray-6">
              {{ template.template }}
            </div>
            <div v-if="template.footer" class="mt-1 text-p-xs text-ink-gray-5">
              {{ template.footer }}
            </div>
          </button>

          <div
            v-if="!filteredTemplates.length"
            class="py-8 text-center text-p-sm text-ink-gray-5"
          >
            {{ __("No approved templates found") }}
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { WhatsAppTemplate } from "@/types";
import { Dialog, TextInput, FeatherIcon, createListResource } from "frappe-ui";
import { computed, ref, watch } from "vue";

const show = defineModel<boolean>();
const emit = defineEmits<{ send: [template: string] }>();

const search = ref("");

// Only Meta-approved templates can be sent; the DocType lives in the
// frappe_whatsapp transport app. `pageLength` is effectively unbounded because
// the whole approved set is filtered client-side.
const templates = createListResource({
  doctype: "WhatsApp Templates",
  cache: "whatsapp-templates",
  fields: ["name", "template", "footer"],
  filters: { status: "APPROVED" },
  orderBy: "modified desc",
  pageLength: 99999,
});

// Fetch lazily on first open — the modal lives in the tree from mount, so
// `auto` would load every approved template even when it's never opened.
watch(show, (open) => {
  if (open && !templates.data) templates.fetch();
});

const filteredTemplates = computed<WhatsAppTemplate[]>(() => {
  const rows: WhatsAppTemplate[] = templates.data || [];
  const query = search.value.toLowerCase().trim();
  if (!query) return rows;
  return rows.filter((t) => t.name.toLowerCase().includes(query));
});
</script>
