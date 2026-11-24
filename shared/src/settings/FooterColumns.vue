<template>
  <div class="flex flex-col gap-3">
    <SettingsRow
      :title="__('Link columns')"
      :description="
        __(
          'Group links under a heading. Each column shows side by side in the footer.'
        )
      "
    />
    <SettingsTable
      v-model="columns"
      :columns="[
        { key: 'title', label: __('Title'), width: '144px' },
        { key: 'links', label: __('Links'), width: 'minmax(0,1fr)' },
      ]"
      :row-label="(column) => column.title"
      :empty-text="__('No columns added yet.')"
    >
      <template #title="{ item: column }">
        <SettingsTableInput
          v-model="column.title"
          class="[&_input]:font-medium"
          :placeholder="__('Company')"
          :aria-label="__('Column title')"
        />
      </template>
      <template #links="{ item: column }">
        <Draggable
          :list="column.links"
          @change="(event) => event.removed && removeIfEmpty(column)"
          :item-key="(link) => link"
          group="footer-links"
          v-bind="DRAG_OPTIONS"
          class="flex min-w-0 flex-1 flex-wrap items-center gap-1.5"
        >
          <template #item="{ element: link, index: linkIndex }">
            <span class="inline-flex">
              <Button
                class="cursor-grab rounded-e-none"
                variant="subtle"
                :label="link.label"
                :title="__('Drag to reorder')"
                @click="editing = { column, linkIndex }"
                @keydown.alt.left.prevent="
                  moveLink($event, column, linkIndex, -1)
                "
                @keydown.alt.right.prevent="
                  moveLink($event, column, linkIndex, 1)
                "
                @keydown.delete.prevent="removeLink(column, linkIndex)"
              />
              <Button
                variant="subtle"
                icon="lucide-x"
                class="rounded-s-none text-ink-gray-5 hover:text-ink-gray-8"
                :label="__('Remove {0}', [link.label])"
                @click="removeLink(column, linkIndex)"
              />
            </span>
          </template>
          <template #footer>
            <Button
              variant="outline"
              icon-left="lucide-plus"
              class="border-dashed"
              :label="__('Add link')"
              @click="editing = { column }"
            />
          </template>
        </Draggable>
      </template>
    </SettingsTable>
    <Button
      class="self-start"
      variant="subtle"
      icon-left="lucide-plus"
      :label="__('Add column')"
      :disabled="columns.length >= MAX_FOOTER_COLUMNS"
      @click="editing = { column: { title: '', links: [] } }"
    />
    <FooterLinkDialog
      v-model:open="isEditing"
      :link="editedLink"
      :column-title="editing?.column.title"
      :is-new-column="isNewColumn"
      @save="saveLink"
    />
  </div>
</template>

<script setup lang="ts">
import { Button, SettingsRow } from "frappe-ui";
import { computed, nextTick, ref } from "vue";
import Draggable from "vuedraggable";
import { type FooterColumn, MAX_FOOTER_COLUMNS } from "../knowledgeBaseFooter";
import type { KnowledgeBaseLink } from "../knowledgeBasePreview";
import { __ } from "../translation";
import { DRAG_OPTIONS, moveItem } from "./tableRows";
import FooterLinkDialog from "./FooterLinkDialog.vue";
import SettingsTable from "./SettingsTable.vue";
import SettingsTableInput from "./SettingsTableInput.vue";

const columns = defineModel<FooterColumn[]>({ required: true });

const editing = ref<{ column: FooterColumn; linkIndex?: number } | null>(null);

const isEditing = computed({
  get: () => Boolean(editing.value),
  set: (open) => {
    if (!open) editing.value = null;
  },
});
const isNewColumn = computed(
  () => editing.value && !columns.value.includes(editing.value.column)
);
const editedLink = computed(
  () => editing.value?.column.links[editing.value.linkIndex]
);

function saveLink(link: KnowledgeBaseLink, columnTitle: string) {
  const { column, linkIndex } = editing.value;
  if (linkIndex === undefined) column.links.push(link);
  else column.links[linkIndex] = link;
  if (isNewColumn.value)
    columns.value = [...columns.value, { ...column, title: columnTitle }];
}

async function moveLink(
  event: KeyboardEvent,
  column: FooterColumn,
  index: number,
  by: number
) {
  const to = index + by;
  if (to < 0 || to >= column.links.length) return;
  moveItem(column.links, index, to);
  const chip = event.currentTarget as HTMLElement;
  await nextTick();
  chip.focus();
}

function removeLink(column: FooterColumn, index: number) {
  column.links.splice(index, 1);
  removeIfEmpty(column);
}

function removeIfEmpty(column: FooterColumn) {
  if (!column.links.length)
    columns.value = columns.value.filter((other) => other !== column);
}
</script>
