import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { HDAgentStatus } from "@/types/doctypes";
import { createListResource, createResource, toast } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, reactive, watch } from "vue";

interface LiveAvailability {
  availability: string;
  changedOn: string;
}

interface AvailabilityEvent {
  agent: string;
  availability: string;
  availability_changed_on: string;
}

// Maps an HD Agent Status `color` value to a solid presence-dot background.
const dotColorMap: Record<string, string> = {
  black: "bg-ink-gray-9",
  gray: "bg-gray-500",
  blue: "bg-blue-500",
  green: "bg-green-600",
  red: "bg-red-500",
  pink: "bg-pink-500",
  orange: "bg-orange-500",
  amber: "bg-amber-500",
  yellow: "bg-yellow-500",
  cyan: "bg-cyan-500",
  teal: "bg-teal-500",
  violet: "bg-violet-500",
  purple: "bg-purple-500",
};

const defaultColor = "bg-surface-gray-5";

export const useAgentStatusStore = defineStore("agentStatus", () => {
  // Set only for sessions that have an HD Agent record; null otherwise.
  const myAgentName = window.agent;

  const statuses = createListResource({
    doctype: "HD Agent Status",
    cache: ["HD Agent Status", "list"],
    fields: ["name", "agent_status", "category", "color", "enable", "status_order"],
    orderBy: "`tabHD Agent Status`.status_order",
    pageLength: 1000,
    auto: true,
  });

  // Live availability keyed by HD Agent name. Seeded by fetches and kept current
  // over the socket — set_my_availability broadcasts to every client, so this is
  // the single source of truth for "who is what right now", including ourselves.
  const liveStatuses = reactive<Record<string, LiveAvailability>>({});

  function applyLive(agent: string, availability?: string, changedOn?: string) {
    if (!agent || !availability) return;
    liveStatuses[agent] = { availability, changedOn: changedOn ?? "" };
  }

  const { $socket } = globalStore();
  $socket.on("agent_availability_updated", (data: AvailabilityEvent) =>
    applyLive(data.agent, data.availability, data.availability_changed_on)
  );

  // Seed our own status from the session payload (auth.get_user already resolves
  // the agent), then let the socket and the optimistic write keep it current — no
  // dedicated fetch and no reload.
  const auth = useAuthStore();
  watch(
    () => auth.availability,
    (availability) =>
      applyLive(myAgentName ?? "", availability, auth.availabilityChangedOn),
    { immediate: true }
  );

  const setMyAvailability = createResource({
    url: "helpdesk.api.agent.set_my_availability",
    onSuccess: () => toast.success(__("Status updated successfully.")),
    onError: () => toast.error(__("Could not update status.")),
  });

  const myStatus = computed(
    () => (myAgentName && liveStatuses[myAgentName]?.availability) || ""
  );

  // Selectable statuses, derived from the same list the presence dots use so the
  // menu and the dots never disagree and we avoid a second server round-trip.
  const statusOptions = computed<string[]>(() =>
    (statuses.data ?? [])
      .filter((s: HDAgentStatus) => s.enable)
      .map((s: HDAgentStatus) => s.agent_status)
  );

  function setMyStatus(status: string) {
    if (!myAgentName || !status || status === myStatus.value) return;
    // Optimistic: update immediately, then roll back if the server rejects it.
    // changedOn is left empty — it is never rendered for our own dot and the
    // socket echo overwrites it with the authoritative server timestamp.
    const previous = liveStatuses[myAgentName];
    applyLive(myAgentName, status);
    setMyAvailability.submit(
      { availability: status },
      {
        // Roll back the optimistic write on failure.
        onError: () => {
          if (previous) liveStatuses[myAgentName] = previous;
          else delete liveStatuses[myAgentName];
        },
      }
    );
  }

  function getStatus(name: string): HDAgentStatus | undefined {
    return statuses.data?.find((s: HDAgentStatus) => s.agent_status === name);
  }

  function statusColor(name: string): string {
    const color = getStatus(name)?.color?.toLowerCase();
    return (color && dotColorMap[color]) || defaultColor;
  }

  return {
    statuses,
    liveStatuses,
    myStatus,
    statusOptions,
    setMyStatus,
    getStatus,
    statusColor,
  };
});
