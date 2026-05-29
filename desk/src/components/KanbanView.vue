<template>
  <div
    v-if="loading"
    class="flex h-full w-full items-center justify-center text-ink-gray-5"
  >
    <LoadingIndicator class="h-6 w-6" />
  </div>
  <div
    v-else-if="!columns.length"
    class="flex h-full w-full items-center justify-center text-ink-gray-5"
  >
    {{ __('Select a "Group By" field to enable the kanban view.') }}
  </div>
  <div v-else class="flex h-full overflow-x-auto px-2 pb-3.5">
    <div
      v-for="col in columns"
      :key="col.key"
      class="flex h-full min-w-72 w-72 shrink-0 flex-col gap-2.5 rounded-lg p-2.5 transition-colors hover:bg-surface-gray-2"
    >
      <!-- Column header -->
      <div class="flex items-center justify-between px-1">
        <div class="flex items-center gap-2 text-base">
          <IndicatorIcon :class="parseColor(col.color || 'gray')" />
          <span class="text-ink-gray-9">{{ col.label }}</span>
          <span class="text-sm text-ink-gray-5">{{ col.cards.length }}</span>
        </div>
      </div>

      <!-- Cards -->
      <Draggable
        :list="col.cards"
        :group="{ name: 'kanban-cards' }"
        :data-column="col.key"
        item-key="name"
        :delay="isTouchScreenDevice() ? 200 : 0"
        animation="180"
        ghost-class="kanban-card-ghost"
        class="flex flex-1 flex-col gap-3 overflow-y-auto"
        @end="(evt) => onDragEnd(evt)"
      >
        <template #item="{ element: row }">
          <div
            class="group flex flex-col gap-2 rounded-lg border border-outline-gray-2 bg-surface-white p-3 text-base text-ink-gray-9 shadow-sm transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-1"
            :data-name="row.name"
          >
            <component
              :is="rowRoute ? 'router-link' : 'div'"
              class="flex flex-col gap-2 cursor-pointer"
              v-bind="{
                to: rowRoute
                  ? {
                      name: rowRoute.name,
                      params: { [rowRoute.prop]: row.name },
                      query: { view: route.query?.view },
                    }
                  : undefined,
              }"
            >
              <!-- Title row: subject + ticket id -->
              <slot name="title" v-bind="{ row }">
                <div class="flex items-start gap-2">
                  <div
                    class="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-surface-gray-3 text-xs font-medium uppercase text-ink-gray-7"
                  >
                    {{ initial(row) }}
                  </div>
                  <div class="line-clamp-2 flex-1 text-sm font-medium">
                    {{ row.subject || "—" }}
                  </div>
                  <span
                    v-if="row.name"
                    class="shrink-0 text-xs text-ink-gray-5"
                  >
                    #{{ row.name }}
                  </span>
                </div>
              </slot>

              <!-- Meta row: assignees + modified -->
              <slot name="fields" v-bind="{ row }">
                <div
                  class="flex items-center justify-between gap-2 pl-7 text-xs text-ink-gray-5"
                >
                  <div class="flex items-center gap-1.5">
                    <div
                      v-if="getAssignees(row).length"
                      class="flex -space-x-1.5"
                    >
                      <Avatar
                        v-for="a in getAssignees(row).slice(0, 3)"
                        :key="a.name"
                        :label="a.label"
                        :image="a.image"
                        size="xs"
                        class="ring-1 ring-surface-white"
                      />
                      <span
                        v-if="getAssignees(row).length > 3"
                        class="ml-1 text-xs text-ink-gray-5"
                      >
                        +{{ getAssignees(row).length - 3 }}
                      </span>
                    </div>
                    <span v-if="row.modified">
                      {{ formatTimeShort(row.modified) }}
                    </span>
                  </div>
                  <Badge
                    v-if="row.priority"
                    :label="row.priority"
                    :theme="priorityTheme(row.priority)"
                    variant="subtle"
                    size="sm"
                  />
                </div>
              </slot>
            </component>

            <!-- Bottom icon row: comments / attachments / sla / actions -->
            <slot name="actions" v-bind="{ row }">
              <div
                class="flex items-center justify-between border-t border-outline-gray-1 pt-2 text-ink-gray-5"
              >
                <div class="flex items-center gap-3 text-xs">
                  <span
                    v-if="row._comment_count"
                    class="flex items-center gap-1"
                    :title="__('Comments')"
                  >
                    <FeatherIcon name="message-circle" class="h-3.5 w-3.5" />
                    {{ row._comment_count }}
                  </span>
                  <span
                    v-if="row.attachment_count"
                    class="flex items-center gap-1"
                    :title="__('Attachments')"
                  >
                    <FeatherIcon name="paperclip" class="h-3.5 w-3.5" />
                    {{ row.attachment_count }}
                  </span>
                  <Tooltip
                    v-if="row.resolution_by || row.first_responded_on"
                    :text="__('SLA')"
                  >
                    <FeatherIcon
                      name="clock"
                      class="h-3.5 w-3.5"
                      :class="slaClass(row)"
                    />
                  </Tooltip>
                </div>
                <KanbanCardActions
                  v-if="doctype === 'HD Ticket'"
                  :ticket="row.name"
                  @posted="$emit('cardUpdated', row.name)"
                />
              </div>
            </slot>
          </div>
        </template>
      </Draggable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import Draggable from "vuedraggable";
import {
  Avatar,
  Badge,
  call,
  FeatherIcon,
  LoadingIndicator,
  toast,
  Tooltip,
} from "frappe-ui";
import { IndicatorIcon } from "./icons";
import KanbanCardActions from "./KanbanCardActions.vue";
import { __ } from "@/translation";
import { formatTimeShort, isTouchScreenDevice, parseColor } from "@/utils";

const PRIORITY_THEME: Record<string, string> = {
  Low: "gray",
  Medium: "blue",
  High: "orange",
  Urgent: "red",
};

function priorityTheme(p: string): string {
  return PRIORITY_THEME[p] || "gray";
}

function getAssignees(row: any) {
  // _assign on Frappe docs is a JSON-encoded array of user emails.
  let raw = row._assign;
  if (!raw) return [];
  if (typeof raw === "string") {
    try {
      raw = JSON.parse(raw);
    } catch {
      return [];
    }
  }
  if (!Array.isArray(raw)) return [];
  return raw.map((email: string) => ({
    name: email,
    label: email.split("@")[0],
    image: undefined,
  }));
}

function slaClass(row: any): string {
  // Green if first response logged, orange if approaching, red if breached.
  if (row.agreement_status === "Fulfilled") return "text-ink-green-3";
  if (row.agreement_status === "Failed") return "text-ink-red-3";
  return "text-ink-gray-5";
}

interface KanbanColumn {
  key: string;
  label: string;
  color?: string;
  cards: any[];
}

interface Props {
  doctype: string;
  rows: any[];
  loading?: boolean;
  groupByField: {
    name: string;
    options: Array<{ label?: string; value: string; color?: string }>;
  };
  rowRoute?: { name: string; prop: string };
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (
    e: "cardMoved",
    payload: { name: string; field: string; value: string }
  ): void;
  (e: "cardUpdated", name: string): void;
}>();

const route = useRoute();

// Terminal lifecycle values are pushed to the right of the board.
const TRAILING_VALUES = ["Resolved", "Closed"];

const columns = computed<KanbanColumn[]>(() => {
  const f = props.groupByField;
  if (!f?.name || !Array.isArray(f.options)) return [];

  const built = f.options.map((opt) => {
    const value = opt.value;
    return {
      key: value || "__empty__",
      label: opt.label || value || __("Empty"),
      color: opt.color,
      cards: (props.rows || []).filter((row) =>
        value ? row[f.name] === value : !row[f.name]
      ),
    };
  });

  const head = built.filter((c) => !TRAILING_VALUES.includes(c.key));
  const tail = TRAILING_VALUES.map((v) =>
    built.find((c) => c.key === v)
  ).filter((c): c is KanbanColumn => !!c);
  return [...head, ...tail];
});

function initial(row: any): string {
  const src = (row.subject || row.name || "?").toString().trim();
  return src.charAt(0).toUpperCase();
}

async function onDragEnd(evt: any) {
  const toColumn = evt?.to?.dataset?.column;
  const fromColumn = evt?.from?.dataset?.column;
  const itemName = evt?.item?.dataset?.name;
  if (!toColumn || !itemName || toColumn === fromColumn) return;

  const card = props.rows.find((r) => r.name === itemName);
  if (!card) return;

  const newValue = toColumn === "__empty__" ? "" : toColumn;
  const previousValue = card[props.groupByField.name];
  if (previousValue === newValue) return;
  card[props.groupByField.name] = newValue;

  try {
    await call("frappe.client.set_value", {
      doctype: props.doctype,
      name: card.name,
      fieldname: { [props.groupByField.name]: newValue },
    });
    emit("cardMoved", {
      name: card.name,
      field: props.groupByField.name,
      value: newValue,
    });
  } catch (err: any) {
    card[props.groupByField.name] = previousValue;
    toast.error(
      err?.message || __("Could not update {0}.", [props.groupByField.name])
    );
  }
}
</script>

<style scoped>
.kanban-card-ghost {
  opacity: 0.4;
  border: 1px dashed var(--outline-gray-3, #d1d5db);
}
</style>
