<template>
  <div
    class="group/folder cursor-pointer rounded-4"
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
          :aria-label="__('Select every article in {0}', [label])"
          class="cursor-pointer"
          @update:modelValue="toggleBranch"
        />
      </div>
      <div
        v-for="(column, i) in list.columns"
        :key="column.key"
        class="overflow-x-hidden"
      >
        <div
          v-if="i === 0"
          class="flex min-w-0 items-center gap-2"
          :style="{ paddingInlineStart: `${depth * 24}px` }"
        >
          <button
            class="flex shrink-0 items-center gap-2"
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
            <SpriteIcon
              v-if="!depth"
              :name="group.group.icon?.replace(/^lucide-/, '') || 'folder'"
              class="size-4 text-ink-gray-7"
            />
            <span
              v-else
              :class="open ? 'lucide-folder-open' : 'lucide-folder'"
              class="size-4 text-ink-gray-6"
              aria-hidden="true"
            />
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
          <Dropdown v-if="actions.length" :options="actions" align="start">
            <Button
              variant="ghost"
              size="sm"
              icon="lucide-ellipsis"
              :aria-label="__('Options for {0}', [label])"
              class="opacity-0 focus:opacity-100 group-hover/folder:opacity-100"
              @click.stop
            />
          </Dropdown>
        </div>

        <LiveRing
          v-else-if="column.key === 'status'"
          :published="published"
          :total="total"
        />

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

        <span
          v-else-if="column.key === 'author'"
          class="block truncate text-base text-ink-gray-7"
        >
          {{
            authors.size === 1
              ? [...authors][0]
              : __("{0} authors", [authors.size])
          }}
        </span>

        <span
          v-else-if="column.type === 'Datetime'"
          class="text-base text-ink-gray-7"
        >
          {{ dayjsLocal(latest(column.key)).fromNow() }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Icon from "@helpdesk/shared/Icon.vue";
import LiveRing from "./LiveRing.vue";
import { categoryAccess } from "@helpdesk/shared/settings/categoryAccess.ts";
import { __ } from "@/translation";
import { Button, Checkbox, Dropdown, dayjsLocal } from "frappe-ui";
import { Icon as SpriteIcon } from "frappe-ui/experimental";
import { computed, inject } from "vue";

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

const label = computed(
  () => props.group.group.category_name || props.group.group.label
);
const ids = computed(() => props.rows.map((row) => row.name));
const all = computed(
  () =>
    ids.value.length > 0 &&
    ids.value.every((id) => list.value.selections.has(id))
);
const some = computed(
  () => !all.value && ids.value.some((id) => list.value.selections.has(id))
);
function toggleBranch() {
  const select = !all.value;
  for (const id of ids.value) {
    if (select) list.value.selections.add(id);
    else list.value.selections.delete(id);
  }
}

const total = computed(() => props.rows.length);
const published = computed(
  () => props.rows.filter((row) => row.status === "Published").length
);
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
