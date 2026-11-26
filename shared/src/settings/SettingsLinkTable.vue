<template>
  <div class="flex flex-col gap-3" role="group" :aria-label="title">
    <SettingsRow :title="title" :description="description" />
    <SettingsTable
      v-model="rows"
      :columns="columns"
      :empty-text="__('No links added yet.')"
      :row-label="(row) => row.label"
    >
      <template #label="{ item: row }">
        <SettingsTableInput
          v-model="row.label"
          :placeholder="__('Contact sales')"
        />
      </template>
      <template #url="{ item: row }">
        <SettingsTableInput
          v-model="row.url"
          :error="linkError(row.url)"
          :pattern="SAFE_LINK_PATTERN"
          :placeholder="__('https://example.com/contact')"
        />
      </template>
      <template #open_in_new_tab="{ item: row }">
        <Checkbox v-model="row.open_in_new_tab" />
      </template>
    </SettingsTable>
    <Button
      class="self-start"
      variant="subtle"
      icon-left="lucide-plus"
      :label="__('Add link')"
      :disabled="rows.some((row) => !row.label?.trim() || !row.url?.trim())"
      @click="rows = [...rows, { label: '', url: '', open_in_new_tab: false }]"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { linkError, SAFE_LINK_PATTERN } from "../utils";
import { Button, Checkbox, SettingsRow } from "frappe-ui";
import type { KnowledgeBaseLink } from "../knowledgeBasePreview";
import SettingsTable from "./SettingsTable.vue";
import SettingsTableInput from "./SettingsTableInput.vue";

defineProps<{ title: string; description?: string }>();

const rows = defineModel<KnowledgeBaseLink[]>({ required: true });

const columns = [
  { key: "label", label: __("Label"), width: "minmax(0,1fr)" },
  { key: "url", label: __("URL"), width: "minmax(0,2fr)" },
  {
    key: "open_in_new_tab",
    label: __("Open in new tab"),
    width: "112px",
    class: "justify-center",
  },
];
</script>
