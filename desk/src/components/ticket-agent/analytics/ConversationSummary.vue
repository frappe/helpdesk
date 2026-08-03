<template>
  <div
    class="flex flex-col rounded-lg border border-outline-gray-1 bg-surface-white p-4"
  >
    <h3 class="text-lg font-semibold text-ink-gray-8">
      {{ __("Conversation summary") }}
    </h3>
    <span class="mb-1 text-base text-ink-gray-5">
      {{ __("Volume and routing for this ticket") }}
    </span>
    <template v-for="(row, index) in rows" :key="row.label">
      <div class="flex items-center justify-between py-1.5 text-p-sm">
        <span class="text-ink-gray-6">{{ row.label }}</span>
        <MultipleAvatar
          v-if="row.avatars"
          :avatars="row.avatars"
          hide-name
          :max="5"
        />
        <Badge
          v-else-if="row.churn"
          :label="row.value"
          theme="red"
          variant="subtle"
          size="sm"
        />
        <span v-else class="font-medium tabular-nums text-ink-gray-8">
          {{ row.value }}
        </span>
      </div>
      <Divider v-if="index < rows.length - 1" />
    </template>
  </div>
</template>

<script setup lang="ts">
import MultipleAvatar from "@/components/MultipleAvatar.vue";
import { __ } from "@/translation";
import { Badge, Divider } from "frappe-ui";
import { computed } from "vue";
import { AnalyticsSummary } from "./types";

const props = defineProps<{ summary: AnalyticsSummary }>();

interface SummaryRow {
  label: string;
  value?: string;
  avatars?: string;
  churn?: boolean;
}

const rows = computed<SummaryRow[]>(() => {
  const summary = props.summary;
  const rows: SummaryRow[] = [
    {
      label: __("Customer messages"),
      value: String(summary.customer_messages),
    },
    { label: __("Agent messages"), value: String(summary.agent_messages) },
    { label: __("Total exchanges"), value: String(summary.total_exchanges) },
    {
      label: __("Internal comments"),
      value: String(summary.internal_comments),
    },
    {
      label: __("Agents involved"),
      value: "–",
      avatars: summary.agents_involved.length
        ? JSON.stringify(summary.agents_involved.map((a) => a.user))
        : undefined,
    },
  ];
  // a visible churn row IS the red flag; healthy tickets show nothing
  const churn = summary.churn;
  if (churn.sla_changes >= 1)
    rows.push(churnRow(__("SLA changed"), churn.sla_changes));
  if (churn.team_changes >= 2)
    rows.push(churnRow(__("Team changes"), churn.team_changes));
  if (churn.reassignments >= 2)
    rows.push(churnRow(__("Reassignments"), churn.reassignments));
  return rows;
});

function churnRow(label: string, count: number): SummaryRow {
  return { label: `⚑ ${label}`, value: `${count}×`, churn: true };
}
</script>
