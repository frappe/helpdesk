<template>
  <div class="rounded-md border border-outline-gray-1 bg-surface-base">
    <div class="flex items-center gap-1.5 px-4 pt-4">
      <h3 class="text-lg font-semibold text-ink-gray-8">
        {{ __("Conversation Summary") }}
      </h3>
    </div>
    <div class="flex flex-col px-4 pb-4 pt-5">
      <div
        v-for="row in rows"
        :key="row.label"
        class="flex items-center justify-between py-2"
        :class="summary.agents_involved.length !== 0 ? 'last:py-0' : ''"
      >
        <span
          class="text-base text-ink-gray-5"
          :class="row.avatars && 'pt-[5px]'"
        >
          {{ row.label }}
        </span>
        <MultipleAvatar
          v-if="row.avatars"
          :avatars="row.avatars"
          hide-name
          :max="5"
          class="pt-2"
          :class="summary.agents_involved.length === 1 ? '!me-0' : ''"
        />
        <span v-else class="text-base text-ink-gray-7">
          {{ row.value }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MultipleAvatar from "@/components/MultipleAvatar.vue";
import { __ } from "@/translation";
import { computed } from "vue";
import { AnalyticsSummary } from "./types";

const props = defineProps<{ summary: AnalyticsSummary }>();

interface SummaryRow {
  label: string;
  value?: string;
  avatars?: string;
}

const rows = computed<SummaryRow[]>(() => {
  const summary = props.summary;
  const rows: SummaryRow[] = [
    {
      label: __("Customer messages"),
      value: String(summary.customer_messages),
    },
    { label: __("Agent replies"), value: String(summary.agent_messages) },
    {
      label: __("Internal comments"),
      value: String(summary.internal_comments),
    },
  ];
  // a visible churn row IS the signal; healthy tickets show nothing
  const churn = summary.churn;
  if (churn.sla_changes >= 1)
    rows.push({ label: __("SLA changed"), value: times(churn.sla_changes) });
  if (churn.team_changes >= 2)
    rows.push({ label: __("Team changed"), value: times(churn.team_changes) });
  const agents: SummaryRow = { label: __("Agents involved"), value: "–" };
  if (summary.agents_involved.length)
    agents.avatars = JSON.stringify(
      summary.agents_involved.map((agent) => ({
        name: agent.name,
        label: agent.name,
        image: agent.image,
      }))
    );
  rows.push(agents);
  return rows;
});

function times(count: number): string {
  return count === 1 ? __("1 time") : __("{0} times", String(count));
}
</script>
