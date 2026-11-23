<template>
  <div class="flex flex-col gap-3" role="group" :aria-label="title">
    <SettingsRow :title="title" :description="description" />
    <SettingsTable
      v-model="rows"
      :columns="columns"
      :empty-text="__('No links added yet.')"
      :row-label="(row) => row.label"
    >
      <template #header>
        <ListHeaderCell class="ms-2">{{ __("Label") }}</ListHeaderCell>
        <ListHeaderCell class="ms-2">{{ __("URL") }}</ListHeaderCell>
        <ListHeaderCell class="justify-center">
          {{ __("Open in new tab") }}
        </ListHeaderCell>
      </template>
      <template #default="{ item: row }">
        <ListCell>
          <TextInput
            v-model="row.label"
            class="w-full [&_input]:text-ellipsis"
            variant="ghost"
            :placeholder="__('Contact sales')"
          />
        </ListCell>
        <ListCell>
          <TextInput
            v-model="row.url"
            :error="linkError(row.url)"
            class="w-full [&_input]:text-ellipsis"
            variant="ghost"
            :placeholder="__('https://example.com/contact')"
          />
        </ListCell>
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
import { linkError } from "../utils";
import { Button, Checkbox, TextInput, SettingsRow } from "frappe-ui";
import { ListCell, ListHeaderCell } from "frappe-ui/list";
import type { KnowledgeBaseLink } from "../knowledgeBasePreview";
import SettingsTable from "./SettingsTable.vue";

defineProps<{ title: string; description?: string }>();

const rows = defineModel<KnowledgeBaseLink[]>({ required: true });

const columns = ["minmax(0,1fr)", "minmax(0,2fr)", "112px"];
</script>
