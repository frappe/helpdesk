import { createResource } from "frappe-ui";
import { computed } from "vue";

const availability = createResource({
  url: "helpdesk.api.agent.get_my_availability",
  auto: true,
});

const setAvailability = createResource({
  url: "helpdesk.api.agent.set_my_availability",
  onSuccess: () => availability.reload(),
});

const statusColorMap: Record<string, string> = {
  Available: "bg-surface-green-3",
  Away: "bg-surface-amber-3",
  Busy: "bg-surface-red-5",
};

export function statusColor(status: string): string {
  return statusColorMap[status] ?? "bg-surface-gray-5";
}

export function useAvailability() {
  const currentStatus = computed(() => availability.data?.availability || "");
  const options = computed(() => availability.data?.options || []);

  function setStatus(status: string) {
    if (status === currentStatus.value) return;
    setAvailability.submit({ availability: status });
  }

  return { currentStatus, options, setStatus };
}
