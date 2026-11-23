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
      :columns="['144px', 'minmax(0,1fr)']"
      :row-label="(column) => column.title"
      :empty-text="__('No columns added yet.')"
    >
      <template #header>
        <ListHeaderCell class="ms-2">{{ __("Title") }}</ListHeaderCell>
        <ListHeaderCell>{{ __("Links") }}</ListHeaderCell>
      </template>
      <template #default="{ item: column }">
        <ListCell>
          <TextInput
            v-model="column.title"
            class="w-full [&_input]:text-ellipsis [&_input]:font-medium"
            variant="ghost"
            :placeholder="__('Company')"
            :aria-label="__('Column title')"
          />
        </ListCell>
        <ListCell>
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
        </ListCell>
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
import { Button, TextInput, SettingsRow } from "frappe-ui";
import { ListCell, ListHeaderCell } from "frappe-ui/list";
import { computed, nextTick, ref } from "vue";
import Draggable from "vuedraggable";
import { type FooterColumn, MAX_FOOTER_COLUMNS } from "../knowledgeBaseFooter";
import type { KnowledgeBaseLink } from "../knowledgeBasePreview";
import { __ } from "../translation";
import { DRAG_OPTIONS, moveItem } from "../utils";
import FooterLinkDialog from "./FooterLinkDialog.vue";
import SettingsTable from "./SettingsTable.vue";

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
  if (isNewColumn.value) columns.value.push({ ...column, title: columnTitle });
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
    columns.value.splice(columns.value.indexOf(column), 1);
}
</script>
