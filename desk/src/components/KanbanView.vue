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
      class="flex h-full min-w-72 w-72 shrink-0 flex-col gap-2.5 rounded-lg p-2.5"
    >
      <!-- Column header -->
      <div class="flex items-center justify-between px-1">
        <div class="flex items-center gap-2 text-base">
          <IndicatorIcon :class="parseColor(col.color)" />
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
        class="flex flex-1 flex-col gap-3.5 overflow-y-auto"
        @end="(evt) => onDragEnd(evt)"
      >
        <template #item="{ element: row }">
          <div
            class="group flex flex-col gap-1.5 rounded-lg bg-surface-white px-3.5 py-3 text-base text-ink-gray-9 hover:bg-surface-gray-1"
            :data-name="row.name"
          >
            <component
              :is="rowRoute ? 'router-link' : 'div'"
              class="flex flex-col gap-1.5 cursor-pointer"
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
              <!-- Title slot — initial badge + subject -->
              <slot name="title" v-bind="{ row }">
                <div class="flex items-start gap-2">
                  <div
                    class="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-surface-gray-3 text-xs font-medium uppercase text-ink-gray-7"
                  >
                    {{ initial(row) }}
                  </div>
                  <div class="line-clamp-2 text-sm">
                    {{ row.subject || "—" }}
                  </div>
                </div>
              </slot>

              <!-- Fields slot -->
              <slot name="fields" v-bind="{ row }">
                <div
                  class="flex items-center gap-2 pl-7 text-xs text-ink-gray-5"
                >
                  <span v-if="row.modified">
                    {{ formatTimeShort(row.modified) }}
                  </span>
                  <span v-if="row.priority" class="text-ink-gray-7">
                    · {{ row.priority }}
                  </span>
                </div>
              </slot>
            </component>

            <!-- Card actions footer (slot, default: HD Ticket comment/reply) -->
            <slot name="actions" v-bind="{ row }">
              <KanbanCardActions
                v-if="doctype === 'HD Ticket'"
                :ticket="row.name"
                @posted="$emit('cardUpdated', row.name)"
              />
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
import { call, LoadingIndicator, toast } from "frappe-ui";
import { IndicatorIcon } from "./icons";
import KanbanCardActions from "./KanbanCardActions.vue";
import { __ } from "@/translation";
import { formatTimeShort, isTouchScreenDevice, parseColor } from "@/utils";

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
