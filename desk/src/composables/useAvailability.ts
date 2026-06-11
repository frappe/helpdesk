import { createResource, toast } from "frappe-ui";
import { computed } from "vue";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";

const availability = createResource({
  url: "helpdesk.api.agent.get_my_availability",
});

const setAvailability = createResource({
  url: "helpdesk.api.agent.set_my_availability",
  onSuccess: () => { availability.reload(); 
    toast.success(__("Status updated successfully."));
  },
});

export function useAvailability() {
  const authStore = useAuthStore();
  if (authStore.isAgent && !availability.fetched) {
    availability.fetch();
  }

  const currentStatus = computed(() => availability.data?.availability || "");
  const options = computed(() => availability.data?.options || []);

  function setStatus(status: string) {
    if (status === currentStatus.value) return;
    setAvailability.submit({ availability: status });
  }

  return { currentStatus, options, setStatus };
}
