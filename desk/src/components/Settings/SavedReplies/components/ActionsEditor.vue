<template>
  <div class="space-y-3">
    <div class="flex flex-col gap-1">
      <span class="text-lg-medium text-ink-gray-8">{{ __("Actions") }}</span>
      <span class="text-p-base text-ink-gray-6">
        {{ __("Applied to the ticket when this reply is sent") }}
      </span>
    </div>
    <Grid
      v-model="rows"
      :columns="columns"
      :error="error"
      :empty-text="
        __(
          'No actions yet. Add one to update the ticket when this reply is sent'
        )
      "
      :add-label="__('Add action')"
      :selectable="false"
      :reorderable="false"
      row-action="remove"
    >
      <template #cell="{ row, column, value, update }">
        <Select
          v-if="column.fieldname === 'action_type'"
          class="w-full"
          :model-value="(value as string)"
          :options="typeOptions(row as ActionRow)"
          :placeholder="__('Select action')"
          @update:model-value="
            setActionType(row as ActionRow, $event as SavedReplyActionType)
          "
        />
        <ActionValue
          v-else-if="row.action_type"
          :type="row.action_type"
          :model-value="value"
          :options="valueOptions(row.action_type)"
          @update:model-value="update"
        />
        <span v-else class="flex items-center px-2 text-p-sm text-ink-gray-4">
          &mdash;
        </span>
      </template>
    </Grid>
  </div>
</template>

<script setup lang="ts">
import { useTags, type Tag } from "@/composables/useTags";
import { useAgentStore } from "@/stores/agent";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import {
  DropdownOption,
  SavedReplyAction,
  SavedReplyActionType,
} from "@/types";
import { Grid, type GridColumn } from "@framework/ui";
import { createListResource, Select } from "frappe-ui";
import { ref, watch } from "vue";
import ActionValue from "./ActionValue.vue";
import {
  ACTION_TYPE_ORDER,
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

const props = defineProps<{
  teamOptions: DropdownOption[];
  error?: string;
}>();

const actions = defineModel<SavedReplyAction[]>({ required: true });

const statusStore = useTicketStatusStore();
const priorityStore = useTicketPriorityStore();
const agentStore = useAgentStore();
const { tagListResource } = useTags();

const ticketTypesResource = createListResource({
  doctype: "HD Ticket Type",
  cache: ["HD Ticket Type", "list"],
  fields: ["name"],
  filters: { disabled: 0 },
  pageLength: 100,
  auto: true,
});

const columns: GridColumn[] = [
  { fieldname: "action_type", label: __("Action"), width: 220 },
  { fieldname: "value", label: __("Value") },
];

// The grid edits rows in place, so it needs a real ref; the flat model is derived.
const rows = ref<ActionRow[]>(toRows(actions.value));

/** Types still free for this row: no duplicates, and one assignment action. */
function typeOptions(row: ActionRow): ActionOption[] {
  const used = new Set(
    rows.value
      .filter((other) => other !== row)
      .map((other) => other.action_type)
  );
  const hasAssignment = ASSIGNMENT_ACTIONS.some((type) => used.has(type));
  return ACTION_TYPE_ORDER.filter(
    (type) =>
      !used.has(type) && !(hasAssignment && ASSIGNMENT_ACTIONS.includes(type))
  ).map((type) => ({
    label: ACTION_TYPES[type].label,
    value: type,
    icon: ACTION_TYPES[type].icon,
  }));
}

/** A value picked for the old type means nothing to the new one. */
function setActionType(row: ActionRow, type: SavedReplyActionType) {
  row.action_type = type;
  row.value = isTagAction(type) ? [] : "";
}

function valueOptions(type: SavedReplyActionType): ActionOption[] {
  switch (type) {
    case "Set Status":
      return (statusStore.statuses.data || [])
        .filter((status) => status.enabled)
        .map((status) => ({
          label: status.label_agent,
          value: status.label_agent,
        }));
    case "Set Priority":
      return (priorityStore.priorities.data || [])
        .filter((priority) => !priority.disabled)
        .map((priority) => ({ label: priority.name, value: priority.name }));
    case "Set Team":
      return props.teamOptions;
    case "Set Ticket Type":
      return (ticketTypesResource.data || []).map(
        (ticketType: { name: string }) => ({
          label: ticketType.name,
          value: ticketType.name,
        })
      );
    case "Assign Agent":
      return agentStore.dropdown || [];
    case "Add Tag":
    case "Remove Tag": {
      // A tag can't be both added and removed by the same reply
      const sibling = type === "Add Tag" ? "Remove Tag" : "Add Tag";
      const taken = new Set(
        rows.value
          .filter((row) => row.action_type === sibling)
          .flatMap((row) => row.value as string[])
      );
      return ((tagListResource.data || []) as Tag[])
        .filter((tag) => !taken.has(tag.name))
        .map((tag) => ({ label: tag.name, value: tag.name, color: tag.color }));
    }
    default:
      return [];
  }
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

if (!agentStore.agents.data) agentStore.agents.fetch();

watch(rows, () => (actions.value = toActions(rows.value)), { deep: true });

// Reseed only on a genuine outside change (the saved reply loading), never on
// our own write-back above.
watch(actions, (list) => {
  if (JSON.stringify(list) !== JSON.stringify(toActions(rows.value)))
    rows.value = toRows(list);
});
</script>
