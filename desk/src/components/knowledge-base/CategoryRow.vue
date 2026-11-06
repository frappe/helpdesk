<template>
  <div
    :id="`kb-category-${group.group.value}`"
    class="group/folder relative cursor-pointer rounded-4"
    :class="
      all
        ? 'bg-surface-gray-2 hover:bg-surface-gray-3'
        : 'hover:bg-surface-sidebar'
    "
    @click="$emit('toggle')"
  >
    <div
      class="grid items-center gap-4 px-2"
      :style="{ height: rowHeight, gridTemplateColumns }"
    >
      <div
        v-if="list.options.selectable"
        class="w-fit pe-2 py-3 flex"
        @click.stop
      >
        <!-- selects every article in the branch -->
        <Checkbox
          :modelValue="all"
          :class="{ 'opacity-60': some }"
          :aria-label="__('Select {0}', [label])"
          class="cursor-pointer"
          @update:modelValue="toggleBranch"
        />
      </div>
      <div
        v-for="(column, i) in list.columns"
        :key="column.key"
        class="min-w-0"
      >
        <div
          v-if="i === 0"
          class="flex min-w-0 items-center gap-2"
          :style="{ paddingInlineStart: `${depth * 24}px` }"
        >
          <button
            class="flex shrink-0 items-center gap-2 rounded focus:outline-none focus-visible:ring focus-visible:ring-outline-gray-3"
            :aria-expanded="open"
            :aria-label="
              open ? __('Collapse {0}', [label]) : __('Expand {0}', [label])
            "
            @click.stop="$emit('toggle')"
          >
            <span
              class="lucide-chevron-right size-4 text-ink-gray-5 transition-transform"
              :class="open ? 'rotate-90' : 'rtl:rotate-180'"
              aria-hidden="true"
            />
            <!-- a plain folder opens with the row; a custom icon stays put -->
            <span
              v-if="icon === 'folder'"
              :class="[open ? 'lucide-folder-open' : 'lucide-folder', iconTone]"
              class="size-4"
              aria-hidden="true"
            />
            <SpriteIcon v-else :name="icon" class="size-4" :class="iconTone" />
          </button>
          <span
            class="min-w-0 truncate"
            :class="
              depth
                ? 'text-base text-ink-gray-8'
                : 'text-base-medium text-ink-gray-9'
            "
          >
            {{ label }}
          </span>
        </div>

        <span
          v-else-if="column.key === 'visibility' && access"
          class="flex min-w-0 items-center gap-1.5 text-base text-ink-gray-7"
        >
          <Icon
            :icon="categoryAccess()[access]?.icon"
            class="h-4 w-4 flex-shrink-0 text-ink-gray-6"
          />
          <span class="truncate">{{ categoryAccess()[access]?.label }}</span>
        </span>

        <MultipleAvatar
          v-else-if="column.key === 'author'"
          :avatars="[...authors]"
          :max="3"
        />

        <span
          v-else-if="column.type === 'Datetime'"
          class="text-base text-ink-gray-7"
        >
          {{ dayjsLocal(latest(column.key)).fromNow() }}
        </span>
      </div>
    </div>
    <!-- at the row's end, as the old group headers had it -->
    <div
      v-if="actions.length"
      class="absolute inset-y-0 end-1 flex items-center"
      @click.stop
    >
      <Dropdown :options="actions" align="end">
        <Button
          variant="ghost"
          icon="lucide-more-horizontal"
          :aria-label="__('Options for {0}', [label])"
        />
      </Dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { MultipleAvatar } from "@/components";
import Icon from "@helpdesk/shared/Icon.vue";
import { categoryAccess } from "@helpdesk/shared/settings/categoryAccess.ts";
import { __ } from "@/translation";
import { Button, Checkbox, Dropdown, dayjsLocal } from "frappe-ui";
import { Icon as SpriteIcon } from "frappe-ui/experimental";
import { computed, inject, watch } from "vue";

// A category or subcategory as a list row; its cells sum up its articles.
const props = defineProps<{
  group: any;
  rows: any[];
  depth: number;
  open: boolean;
  actions: any[];
}>();
defineEmits<{ toggle: [] }>();

const list = inject<any>("list");
const tickedCategories = inject<Set<string>>("tickedCategories");

const label = computed(
  () => props.group.group.category_name || props.group.group.label
);
const icon = computed(
  () => props.group.group.icon?.replace(/^lucide-/, "") || "folder"
);
const iconTone = computed(() =>
  props.depth ? "text-ink-gray-6" : "text-ink-gray-7"
);
const ids = computed(() => props.rows.map((row) => row.name));
const value = computed(() => props.group.group.value);
const filled = computed(
  () =>
    ids.value.length > 0 &&
    ids.value.every((id) => list.value.selections.has(id))
);
// the header's select all ticks every category
watch(
  () => list.value.allRowsSelected,
  (selected) => selected && tickedCategories.add(value.value),
  { immediate: true }
);
// checked only when this category, or its parent, was ticked; articles picked one
// by one leave it partly checked
const all = computed(
  () =>
    filled.value &&
    (tickedCategories.has(value.value) ||
      tickedCategories.has(props.group.group.parent_article_category))
);
const some = computed(
  () => !all.value && ids.value.some((id) => list.value.selections.has(id))
);
watch(filled, (isFilled) => {
  if (!isFilled) tickedCategories.delete(value.value);
});
function toggleBranch() {
  const select = !all.value;
  for (const id of ids.value) {
    if (select) list.value.selections.add(id);
    else list.value.selections.delete(id);
  }
  if (select) tickedCategories.add(value.value);
  else tickedCategories.delete(value.value);
}

const access = computed(() => {
  const values = new Set(props.rows.map((row) => row.visibility));
  return values.size > 1 ? "Mixed" : [...values][0];
});
const authors = computed(() => new Set(props.rows.map((row) => row.author)));
const latest = (key: string) =>
  props.rows
    .map((row) => row[key])
    .sort()
    .at(-1);

// same grid as frappe-ui's ListRow
const gridTemplateColumns = computed(
  () =>
    (list.value.options.selectable ? "14px " : "") +
    list.value.columns
      .map((column) =>
        typeof (column.width || 1) === "number"
          ? `${column.width || 1}fr`
          : column.width
      )
      .join(" ")
);
const rowHeight = computed(() => {
  const height = list.value.options.rowHeight;
  return typeof height === "number" ? `${height}px` : height;
});
</script>
