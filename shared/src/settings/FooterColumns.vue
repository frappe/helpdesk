<template>
  <div class="flex flex-col gap-3">
    <SettingsHeading
      :title="__('Link columns')"
      :description="
        __(
          'Group links under a heading. Each column shows side by side in the footer.'
        )
      "
    />
    <SettingsTable
      v-model="columns"
      :columns="['144px', 'minmax(0,1fr)', '32px']"
      :empty-text="__('No columns added yet.')"
    >
      <template #header>
        <ListHeaderCell class="ms-2">{{ __("Title") }}</ListHeaderCell>
        <ListHeaderCell>{{ __("Links") }}</ListHeaderCell>
        <ListHeaderCell />
      </template>
      <template #default="{ item: column, index }">
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
              <span class="group/chip relative inline-flex">
                <Button
                  class="cursor-grab"
                  size="sm"
                  variant="subtle"
                  :icon-right="
                    link.open_in_new_tab ? 'lucide-arrow-up-right' : undefined
                  "
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
                <button
                  type="button"
                  class="absolute -end-1.5 -top-1.5 flex size-4 items-center justify-center rounded-full bg-surface-gray-7 text-ink-white opacity-0 shadow-sm transition-opacity focus-visible:opacity-100 group-hover/chip:opacity-100"
                  :aria-label="__('Remove {0}', [link.label])"
                  @click="removeLink(column, linkIndex)"
                >
                  <span class="lucide-x size-3" aria-hidden="true" />
                </button>
              </span>
            </template>
            <template #footer>
              <button
                type="button"
                class="flex h-7 items-center gap-1.5 rounded-4 border border-dashed border-outline-gray-3 px-2 text-base text-ink-gray-6 hover:border-outline-gray-4 hover:text-ink-gray-8"
                @click="editing = { column }"
              >
                <span class="lucide-plus size-4" aria-hidden="true" />
                {{ __("Add link") }}
              </button>
            </template>
          </Draggable>
        </ListCell>
        <ListCell class="h-7">
          <Dropdown
            align="end"
            :options="columnOptions(index)"
            @update:open="(open) => open && (isConfirmingDelete = false)"
          >
            <Button
              variant="ghost"
              icon="lucide-more-horizontal"
              :label="__('Options for {0}', [column.title || __('Untitled')])"
            />
          </Dropdown>
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
import { Button, Dropdown, TextInput } from "frappe-ui";
import { ListCell, ListHeaderCell } from "frappe-ui/list";
import { computed, nextTick, ref } from "vue";
import Draggable from "vuedraggable";
import { type FooterColumn, MAX_FOOTER_COLUMNS } from "../knowledgeBaseFooter";
import type { KnowledgeBaseLink } from "../knowledgeBasePreview";
import { __ } from "../translation";
import { DRAG_OPTIONS, ListItemOptions, moveItem } from "../utils";
import FooterLinkDialog from "./FooterLinkDialog.vue";
import SettingsHeading from "./SettingsHeading.vue";
import SettingsTable from "./SettingsTable.vue";

const columns = defineModel<FooterColumn[]>({ required: true });

const isConfirmingDelete = ref(false);

const columnOptions = (index: number) =>
  ListItemOptions(columns.value, index, isConfirmingDelete);
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
