<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-col gap-1">
      <span class="text-base-medium text-ink-gray-8">
        {{ __("Quick links") }}
      </span>
      <span class="text-p-sm text-ink-gray-6">
        {{
          __(
            "Add links to your website, docs or social pages. They will appear at the top right of every knowledge base page."
          )
        }}
      </span>
    </div>
    <div class="rounded-5 border border-outline-gray-2 px-1 text-sm">
      <List
        v-if="rows.length"
        :columns="columns"
        :row-height="44"
        class="[--list-gap:1rem] [--list-row-padding-x:0.5rem]"
      >
        <ListHeader>
          <ListHeaderCell class="ms-2">{{ __("Label") }}</ListHeaderCell>
          <ListHeaderCell class="ms-2">{{ __("URL") }}</ListHeaderCell>
          <ListHeaderCell class="justify-center">
            {{ __("Open in new tab") }}
          </ListHeaderCell>
          <ListHeaderCell />
        </ListHeader>
        <ListRows :items="rows" v-slot="{ item: row, index }">
          <ListRow>
            <ListCell>
              <TextInput
                v-model="row.label"
                class="w-full"
                variant="ghost"
                :placeholder="__('Contact sales')"
              />
            </ListCell>
            <ListCell>
              <TextInput
                v-model="row.url"
                class="w-full"
                variant="ghost"
                :placeholder="__('https://example.com/contact')"
              />
            </ListCell>
            <ListCell class="justify-center">
              <Checkbox v-model="row.open_in_new_tab" />
            </ListCell>
            <ListCell>
              <Dropdown
                align="end"
                :options="rowOptions(index)"
                @update:open="(open) => open && (isConfirmingDelete = false)"
              >
                <Button
                  variant="ghost"
                  icon="lucide-more-horizontal"
                  :label="__('Row actions')"
                />
              </Dropdown>
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
      <div v-else class="p-4 text-center text-ink-gray-5">
        {{ __("No links added yet.") }}
      </div>
    </div>
    <Button
      class="self-start"
      variant="subtle"
      icon-left="lucide-plus"
      :label="__('Add link')"
      @click="rows.push({ label: '', url: '', open_in_new_tab: false })"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { ConfirmDelete } from "../utils";
import { Button, Checkbox, Dropdown, TextInput } from "frappe-ui";
import {
  List,
  ListCell,
  ListHeader,
  ListHeaderCell,
  ListRow,
  ListRows,
} from "frappe-ui/list";
import { ref } from "vue";

type HeaderLink = { label: string; url: string; open_in_new_tab: boolean };

const rows = defineModel<HeaderLink[]>({ required: true });

const columns = ["minmax(0,1fr)", "minmax(0,2fr)", "112px", "32px"];

const isConfirmingDelete = ref(false);

function rowOptions(index: number) {
  return ConfirmDelete({
    isConfirmingDelete,
    onConfirmDelete: () => rows.value.splice(index, 1),
  });
}
</script>
