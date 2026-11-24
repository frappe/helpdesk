<template>
  <div class="flex flex-col gap-3">
    <SettingsRow :title="text.title" :description="text.description" />
    <SettingsTable
      v-model="pinned"
      :columns="columns"
      :empty-text="text.empty"
      :row-label="labelOf"
      :remove="{ label: __('Unpin'), icon: 'lucide-pin-off' }"
    >
      <template #name="{ item: name }">
        <span class="truncate text-base text-ink-gray-8">
          {{ labelOf(name) }}
        </span>
      </template>
      <template #access="{ item: name }">
        <CategoryAccessBadge :access="byName[name]?.access" />
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
import { Button, SettingsRow } from "frappe-ui";
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

const open = ref(false);
const text = computed(() => pinnedListText(props.kind));

const columns = computed(() => [
  { key: "name", label: text.value.column, width: "minmax(0,1fr)" },
  { key: "access", label: __("Visibility"), width: "112px" },
]);

const byName = computed(() =>
  Object.fromEntries(props.items.map((row) => [row.value, row]))
);

function labelOf(name: string) {
  return byName.value[name]?.label || name;
}
</script>
