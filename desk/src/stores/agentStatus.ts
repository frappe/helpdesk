import { globalStore } from "@/stores/globalStore";
import { HDAgentStatus } from "@/types/doctypes";
import { createListResource } from "frappe-ui";
import { defineStore } from "pinia";
import { reactive } from "vue";

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
  gray: "bg-surface-gray-6",
  blue: "bg-surface-blue-6",
  green: "bg-surface-green-6",
  red: "bg-surface-red-6",
  pink: "bg-surface-pink-6",
  orange: "bg-surface-orange-6",
  amber: "bg-surface-amber-6",
  yellow: "bg-surface-yellow-6",
  cyan: "bg-surface-cyan-6",
  teal: "bg-surface-teal-6",
  violet: "bg-surface-violet-6",
  purple: "bg-surface-purple-6",
};

const defaultColor = "bg-surface-gray-8";

export const useAgentStatusStore = defineStore("agentStatus", () => {
  const statuses = createListResource({
    doctype: "HD Agent Status",
    cache: ["HD Agent Status", "list"],
    fields: ["name", "agent_status", "category", "color", "enable", "status_order"],
    orderBy: "`tabHD Agent Status`.status_order",
    pageLength: 1000,
    auto: true,
  });

  // Live availability pushed over the socket when an agent changes their
  // status (helpdesk.api.agent.set_my_availability). Keyed by HD Agent name,
  // it overrides the value fetched when a list first loaded.
  const liveStatuses = reactive<Record<string, LiveAvailability>>({});

  const { $socket } = globalStore();
  $socket.on("agent_availability_updated", (data: AvailabilityEvent) => {
    liveStatuses[data.agent] = {
      availability: data.availability,
      changedOn: data.availability_changed_on,
    };
  });

  function getStatus(name: string): HDAgentStatus | undefined {
    return statuses.data?.find((s: HDAgentStatus) => s.agent_status === name);
  }

  function statusColor(name: string): string {
    const color = getStatus(name)?.color?.toLowerCase();
    return (color && dotColorMap[color]) || defaultColor;
  }

  return { statuses, liveStatuses, getStatus, statusColor };
});
