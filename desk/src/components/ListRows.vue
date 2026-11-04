<template>
  <!-- grouped rows are KB categories, shown as a tree -->
  <div
    class="mx-3 h-full overflow-y-auto sm:mx-5 [&_.h-px.border-t]:hidden"
    v-if="showGroupedRows"
    id="list-rows"
  >
    <template v-for="(item, i) in items" :key="item.key">
      <div v-if="i" class="mx-2 h-px bg-surface-gray-1" />
      <CategoryRow
        v-if="item.folder"
        :group="item.group"
        :rows="item.rows"
        :depth="item.depth"
        :open="isOpen(item.group, item.depth)"
        :actions="actions(item.group)"
        @toggle="toggle(item.group, item.depth)"
      />
      <ListRow
        v-else
        v-slot="{ idx, column, item: value }"
        :row="item.row"
        class="truncate text-base"
      >
        <div
          v-if="idx === 0"
          :style="{ paddingInlineStart: `${item.depth * 24 + 24}px` }"
        >
          <slot v-bind="{ idx, column, item: value, row: item.row }" />
        </div>
        <slot v-else v-bind="{ idx, column, item: value, row: item.row }" />
      </ListRow>
    </template>
  </div>
  <ListRows class="mx-3 sm:mx-5" v-else id="list-rows">
    <ListRow
      v-for="row in rows"
      :key="row.name"
      v-slot="{ idx, column, item }"
      :row="row"
      class="truncate text-base"
    >
      <slot v-bind="{ idx, column, item, row }" />
    </ListRow>
  </ListRows>
</template>

<script setup>
import CategoryRow from "@/components/knowledge-base/CategoryRow.vue";
import { __ } from "@/translation";
import { ListRow, ListRows } from "frappe-ui/experimental";
import { computed, nextTick, reactive, watch } from "vue";

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  groupByActions: {
    type: Array,
    default: () => [],
  },
  // a category to open alone and scroll to
  revealGroup: {
    type: String,
    default: null,
  },
});

// categories start open, subcategories closed; a choice survives reloads
const open = reactive({});
const isOpen = (group, depth) => open[group.group.value] ?? depth === 0;
const toggle = (group, depth) =>
  (open[group.group.value] = !isOpen(group, depth));

// opens only that category and its parent
let revealed = null;
watch(
  () => [props.revealGroup, props.rows],
  ([name]) => {
    if (!name || name === revealed) return;
    const group = props.rows.find((g) => g.group?.value === name);
    if (!group) return;
    revealed = name;
    const parent = group.group.parent_article_category;
    for (const g of props.rows) {
      open[g.group.value] = g.group.value === name || g.group.value === parent;
    }
    nextTick(() =>
      document
        .getElementById(`kb-category-${name}`)
        ?.scrollIntoView({ block: "center" })
    );
  },
  { immediate: true }
);

// flattened in display order: a category, its subcategories, then its own articles
const items = computed(() => {
  const values = new Set(props.rows.map((g) => g.group.value));
  const subsOf = (g) =>
    props.rows.filter((s) => s.group.parent_article_category === g.group.value);
  const folder = (group, depth, rows) => ({
    key: `group:${group.group.value}`,
    folder: true,
    group,
    depth,
    rows,
  });
  const articles = (rows, depth) =>
    rows.map((row) => ({ key: row.name, row, depth }));

  return props.rows
    .filter((g) => !values.has(g.group.parent_article_category))
    .flatMap((top) => {
      const subs = subsOf(top);
      const branch = [...top.rows, ...subs.flatMap((s) => s.rows)];
      const out = [folder(top, 0, branch)];
      if (!isOpen(top, 0)) return out;
      for (const sub of subs) {
        out.push(folder(sub, 1, sub.rows));
        if (isOpen(sub, 1)) out.push(...articles(sub.rows, 2));
      }
      out.push(...articles(top.rows, 1));
      return out;
    });
});

// the Archived group is no category, so it has no actions
const actions = (group) => {
  if (!group.group.value) return [];
  const items = props.groupByActions
    .filter((action) => action.condition?.(group) ?? true)
    .map(({ condition, ...action }) => ({
      ...action,
      onClick: () => action.onClick(group),
    }));
  const danger = items.filter((action) => action.theme === "red");
  // red actions sit below a divider, as ConfirmDelete's do
  return [
    ...items.filter((action) => action.theme !== "red"),
    ...(danger.length
      ? [{ group: __("Danger"), hideLabel: true, options: danger }]
      : []),
  ];
};

const showGroupedRows = computed(() => {
  return props.rows.every(
    (row) => row.group && row.rows && Array.isArray(row.rows)
  );
});
</script>
