<template>
  <div class="flex flex-col gap-3" role="group" :aria-label="title">
    <SettingsRow :title="title" :description="description" />
    <SettingsTable
      v-model="rows"
      :columns="columns"
      :empty-text="__('No links added yet.')"
      :row-label="(row) => row.label"
    >
      <template #default="{ item: row }">
        <SettingsTableInput
          v-model="row.label"
          :placeholder="__('Contact sales')"
        />
        <SettingsTableInput
          v-model="row.url"
          :error="linkError(row.url)"
          :pattern="SAFE_LINK_PATTERN"
          :placeholder="__('https://example.com/contact')"
        />
        <ListCell class="h-7 justify-center">
          <Checkbox v-model="row.open_in_new_tab" />
        </ListCell>
      </template>
    </SettingsTable>
    <Button
      class="self-start"
      variant="subtle"
      icon-left="lucide-plus"
      :label="__('Add link')"
      :disabled="rows.some((row) => !row.label?.trim() || !row.url?.trim())"
      @click="rows.push({ label: '', url: '', open_in_new_tab: false })"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { linkError, SAFE_LINK_PATTERN } from "../utils";
import { Button, Checkbox, SettingsRow } from "frappe-ui";
import { ListCell } from "frappe-ui/list";
import type { KnowledgeBaseLink } from "../knowledgeBasePreview";
import SettingsTable from "./SettingsTable.vue";
import SettingsTableInput from "./SettingsTableInput.vue";

defineProps<{ title: string; description?: string }>();

const rows = defineModel<KnowledgeBaseLink[]>({ required: true });

const columns = [
  { label: __("Label"), width: "minmax(0,1fr)", class: "ms-2" },
  { label: __("URL"), width: "minmax(0,2fr)", class: "ms-2" },
  { label: __("Open in new tab"), width: "112px", class: "justify-center" },
];
</script>
