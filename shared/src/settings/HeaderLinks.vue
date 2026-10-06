<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-col gap-1">
      <span class="text-base-medium text-ink-gray-8">
        {{ __("Quick links") }}
      </span>
      <span class="text-p-sm text-ink-gray-6">
        {{ __("Shown at the top right of every knowledge base page.") }}
      </span>
    </div>
    <div class="rounded-5 border border-outline-gray-2 px-1 text-sm">
      <template v-if="rows.length">
        <div
          class="grid items-center gap-4 p-2"
          :style="{ gridTemplateColumns }"
        >
          <span class="ms-2 text-ink-gray-5">{{ __("Label") }}</span>
          <span class="ms-2 text-ink-gray-5">{{ __("URL") }}</span>
          <span class="text-ink-gray-5">{{ __("New tab") }}</span>
          <span />
        </div>
        <hr />
        <template v-for="(row, index) in rows" :key="index">
          <div
            class="grid items-center gap-4 p-2"
            :style="{ gridTemplateColumns }"
          >
            <TextInput
              v-model="row.label"
              variant="ghost"
              :placeholder="__('Contact sales')"
            />
            <TextInput
              v-model="row.url"
              variant="ghost"
              :placeholder="__('https://example.com/contact')"
            />
            <Checkbox
              v-model="row.open_in_new_tab"
              class="justify-self-center"
            />
            <Button
              variant="ghost"
              icon="lucide-trash-2"
              :label="__('Delete')"
              @click="rows.splice(index, 1)"
            />
          </div>
          <hr v-if="index !== rows.length - 1" />
        </template>
      </template>
      <div v-else class="p-4 text-center text-ink-gray-5">
        {{ __("No links yet. Add one to show it in the portal header") }}
      </div>
    </div>
    <div class="flex items-center justify-between">
      <Button
        variant="subtle"
        icon-left="lucide-plus"
        :label="__('Add link')"
        @click="rows.push({ label: '', url: '', open_in_new_tab: false })"
      />
      <Button
        v-if="isDirty"
        variant="solid"
        :label="__('Save')"
        :loading="saveLinks.loading"
        @click="saveLinks.submit()"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { getErrorMessage } from "../utils";
import { Button, Checkbox, createResource, TextInput, toast } from "frappe-ui";
import { computed, ref, watch } from "vue";

type HeaderLink = { label: string; url: string; open_in_new_tab: boolean };

const props = defineProps<{ links: HeaderLink[] }>();
const emit = defineEmits<{ saved: [] }>();

const gridTemplateColumns = "1fr 2fr 64px 32px";

const rows = ref<HeaderLink[]>([]);

// Only the editable fields, so the saved rows' name and idx don't count as edits.
function pick(links: HeaderLink[]) {
  return links.map(({ label, url, open_in_new_tab }) => ({
    label: label || "",
    url: url || "",
    open_in_new_tab: Boolean(open_in_new_tab),
  }));
}

const saved = computed(() => JSON.stringify(pick(props.links)));

watch(saved, (links) => (rows.value = JSON.parse(links)), { immediate: true });

// Saved here, not through the tab's doc: its optimistic setValue would wipe the rows on a rejection.
const saveLinks = createResource({
  url: "frappe.client.set_value",
  makeParams: () => ({
    doctype: "HD Settings",
    name: "HD Settings",
    fieldname: { portal_header_links: pick(rows.value) },
  }),
  onSuccess: () => {
    toast.success(__("Settings updated"));
    emit("saved");
  },
  onError: (error) => getErrorMessage(error, true),
});

const isDirty = computed(
  () => JSON.stringify(pick(rows.value)) !== saved.value
);
</script>
