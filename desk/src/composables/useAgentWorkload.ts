import { createResource } from "frappe-ui";
import { Ref, watch } from "vue";

interface AgentWorkloadStats {
  open_tickets: number;
  open_tickets_delta: number;
  resolved_today: number;
  average_first_response_seconds: number;
  average_first_response_seconds_delta: number;
  teams: string[];
  team_open_tickets: number;
}

const EMPTY_STATS: AgentWorkloadStats = {
  open_tickets: 0,
  open_tickets_delta: 0,
  resolved_today: 0,
  average_first_response_seconds: 0,
  average_first_response_seconds_delta: 0,
  teams: [],
  team_open_tickets: 0,
};

/**
 * Fetches per-agent workload stats whenever the given agents list changes
 * and exposes a selector for each visible row.
 */
export function useAgentWorkload(agents: Ref<{ name: string }[] | undefined>) {
  const workload = createResource({
    url: "helpdesk.api.agent.get_agent_workload",
    makeParams: () => ({ user_ids: agents.value?.map((a) => a.name) ?? [] }),
  });

  watch(
    () => agents.value?.map((a) => a.name).join(","),
    (ids) => {
      if (ids) workload.fetch();
    },
    { immediate: true }
  );

  function statsFor(agentName: string): AgentWorkloadStats {
    return workload.data?.[agentName] ?? EMPTY_STATS;
  }

  return { statsFor };
}
