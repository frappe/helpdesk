<template>
  <div class="space-y-3">
    <div class="flex flex-col gap-1">
      <span class="text-lg-medium text-ink-gray-8">{{ __("Actions") }}</span>
      <span class="text-p-base text-ink-gray-6">
        {{ __("Applied to the ticket when this reply is sent") }}
      </span>
    </div>
    <div class="rounded-md border border-outline-gray-2 px-1 text-sm">
      <template v-if="rows.length">
        <div
          class="grid items-center gap-6 p-2"
          :style="{ gridTemplateColumns }"
        >
          <div
            v-for="column in columns"
            :key="column.key"
            class="ms-2 overflow-hidden text-ellipsis whitespace-nowrap text-ink-gray-5"
          >
            {{ column.label }}
          </div>
        </div>
        <hr />
        <template v-for="(row, index) in rows" :key="index">
          <div
            class="grid items-center gap-6 p-2"
            :style="{ gridTemplateColumns }"
          >
            <Combobox
              class="w-full"
              variant="ghost"
              trigger="button"
              :model-value="row.action_type"
              :options="typeOptions(row)"
              :placeholder="__('Select action')"
              @update:model-value="
                setActionType(row, $event as SavedReplyActionType)
              "
            />
            <ActionValue
              v-if="row.action_type"
              :type="row.action_type"
              :model-value="row.value"
              :options="valueOptions(row.action_type)"
              @update:model-value="row.value = $event"
              @search="search(row.action_type, $event)"
            />
            <span
              v-else
              class="flex items-center px-2 text-p-sm text-ink-gray-4"
            >
              &mdash;
            </span>
            <div class="flex justify-end">
              <Dropdown
                placement="right"
                :options="[
                  {
                    label: __('Delete'),
                    icon: 'lucide-trash-2',
                    onClick: () => rows.splice(index, 1),
                  },
                ]"
              >
                <Button
                  variant="ghost"
                  icon="lucide-more-horizontal"
                  :label="__('Row actions')"
                />
              </Dropdown>
            </div>
          </div>
          <hr v-if="index !== rows.length - 1" />
        </template>
      </template>
      <div v-else class="p-4 text-center text-ink-gray-5">
        {{
          __(
            "No actions yet. Add one to update the ticket when this reply is sent"
          )
        }}
      </div>
    </div>
    <div class="mt-2.5 flex items-center justify-between">
      <Button
        variant="subtle"
        icon-left="lucide-plus"
        :label="__('Add action')"
        @click="rows.push({ value: '' })"
      />
      <ErrorMessage :message="error" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSavedReplyActionOptions } from "@/composables/useSavedReplyActionOptions";
import { __ } from "@/translation";
import { SavedReplyAction, SavedReplyActionType } from "@/types";
import { getGridTemplateColumnsForTable } from "@/utils";
import { Button, Combobox, Dropdown } from "frappe-ui";
import { computed, ref, watch } from "vue";
import ActionValue from "./ActionValue.vue";
import {
  ACTION_MENU_GROUPS,
  ACTION_TYPES,
  ASSIGNMENT_ACTIONS,
  isTagAction,
  type ActionOption,
} from "./actionTypes";

/** One grid row. Tag rows hold every selected tag; the model stores one per tag. */
type ActionRow = {
  action_type?: SavedReplyActionType;
  value: string | string[];
};

defineProps<{
  error?: string;
}>();

const actions = defineModel<SavedReplyAction[]>({ required: true });

const {
  valueOptions: sharedValueOptions,
  tagOptions,
  search,
} = useSavedReplyActionOptions();

const columns = [
  { key: "action_type", label: __("Action"), width: "190px" },
  { key: "value", label: __("Value") },
];

// Trailing 22px column holds the remove button
const gridTemplateColumns = computed(() =>
  getGridTemplateColumnsForTable(columns)
);

// The table edits rows in place, so it needs a real ref; the flat model is derived.
const rows = ref<ActionRow[]>(toRows(actions.value));

/** Types still free for this row: no duplicates, and one assignment action. */
function typeOptions(row: ActionRow) {
  const used = new Set(
    rows.value
      .filter((other) => other !== row)
      .map((other) => other.action_type)
  );
  const hasAssignment = ASSIGNMENT_ACTIONS.some((type) => used.has(type));
  return ACTION_MENU_GROUPS.map((group) => ({
    group: group.label,
    options: group.types
      .filter(
        (type) =>
          !used.has(type) &&
          !(hasAssignment && ASSIGNMENT_ACTIONS.includes(type))
      )
      .map((type) => ({
        label: ACTION_TYPES[type].label,
        value: type,
        icon: ACTION_TYPES[type].icon,
      })),
  })).filter((group) => group.options.length);
}

/** A value picked for the old type means nothing to the new one. */
function setActionType(row: ActionRow, type: SavedReplyActionType) {
  row.action_type = type;
  row.value = isTagAction(type) ? [] : "";
}

/** Shared lists, minus the tags the opposite row already claimed. */
function valueOptions(type: SavedReplyActionType): ActionOption[] {
  if (!isTagAction(type)) return sharedValueOptions(type);
  // A tag can't be both added and removed by the same reply
  const sibling = type === "Add Tag" ? "Remove Tag" : "Add Tag";
  const taken = new Set(
    rows.value
      .filter((row) => row.action_type === sibling)
      .flatMap((row) => row.value as string[])
  );
  return tagOptions().filter((tag) => !taken.has(String(tag.value)));
}

function toRows(list: SavedReplyAction[]): ActionRow[] {
  const grouped: ActionRow[] = [];
  for (const action of list) {
    const tagRow = isTagAction(action.action_type)
      ? grouped.find((row) => row.action_type === action.action_type)
      : undefined;
    if (tagRow) (tagRow.value as string[]).push(action.value);
    else
      grouped.push({
        action_type: action.action_type,
        value: isTagAction(action.action_type) ? [action.value] : action.value,
      });
  }
  return grouped;
}

/** Rows with no type yet (or no tags picked) simply don't persist. */
function toActions(list: ActionRow[]): SavedReplyAction[] {
  return list.flatMap((row) => {
    const type = row.action_type;
    if (!type) return [];
    if (Array.isArray(row.value))
      return row.value.map((value) => ({ action_type: type, value }));
    return [{ action_type: type, value: row.value }];
  });
}

watch(rows, () => (actions.value = toActions(rows.value)), { deep: true });

// Reseed only on a genuine outside change (the saved reply loading), never on
// our own write-back above.
watch(actions, (list) => {
  if (JSON.stringify(list) !== JSON.stringify(toActions(rows.value)))
    rows.value = toRows(list);
});
</script>
