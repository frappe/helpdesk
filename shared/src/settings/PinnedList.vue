<template>
  <div class="flex flex-col gap-3">
    <SettingsRow :title="text.title" :description="text.description" />
    <SettingsTable
      v-model="pinned"
      :columns="columns"
      :empty-text="text.empty"
      :row-label="labelOf"
      :options="rowOptions"
    >
      <template #header>
        <ListHeaderCell>{{ text.column }}</ListHeaderCell>
        <ListHeaderCell>{{ __("Visibility") }}</ListHeaderCell>
      </template>
      <template #default="{ item: name }">
        <ListCell class="h-7">
          <span class="truncate text-base text-ink-gray-8">
            {{ labelOf(name) }}
          </span>
        </ListCell>
        <ListCell class="h-7">
          <CategoryAccessBadge :access="byName[name]?.access" />
        </ListCell>
      </template>
    </SettingsTable>
    <Button
      class="self-start"
      variant="subtle"
      icon-left="lucide-plus"
      :label="text.add"
      :disabled="kind === 'articles' && pinned.length >= MAX_PINNED_ARTICLES"
      @click="open = true"
    />
    <PinnedListDialog
      v-model:open="open"
      :kind="kind"
      :items="items"
      :pinned="pinned"
      :save="save"
      :search="search"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { moveOptions, moveItem } from "../utils";
import { Button, SettingsRow } from "frappe-ui";
import { ListCell, ListHeaderCell } from "frappe-ui/list";
import { computed, ref } from "vue";
import CategoryAccessBadge from "./CategoryAccessBadge.vue";
import { MAX_PINNED_ARTICLES, type PinKind } from "./knowledgeBaseDraft";
import PinnedListDialog from "./PinnedListDialog.vue";
import SettingsTable from "./SettingsTable.vue";
import { pinnedListText } from "./pinnedListText";

type Item = {
  label: string;
  value: string;
  access?: string;
};

const props = defineProps<{
  kind: PinKind;
  items: Item[];
  save: (pinned: string[]) => Promise<boolean>;
  search?: (query: string) => void;
}>();

const pinned = defineModel<string[]>("pinned", { required: true });

const columns = ["minmax(0,1fr)", "112px"];

const open = ref(false);
const text = computed(() => pinnedListText(props.kind));

const byName = computed(() =>
  Object.fromEntries(props.items.map((row) => [row.value, row]))
);

function labelOf(name: string) {
  return byName.value[name]?.label || name;
}

function rowOptions(index: number) {
  return [
    ...moveOptions(index, pinned.value.length, (to) => {
      const next = [...pinned.value];
      moveItem(next, index, to);
      pinned.value = next;
    }),
    {
      label: __("Unpin"),
      icon: "lucide-pin-off",
      onClick: () =>
        (pinned.value = pinned.value.filter((_, i) => i !== index)),
    },
  ];
}
</script>
