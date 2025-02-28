import { computed } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

export const useAgentStore = defineStore("agent", () => {
  const agents = createListResource({
    doctype: "HD Agent",
    fields: ["name", "agent_name", "user", "user.user_image"],
    filters: { is_active: 1 },
    pageLength: 99999,
  });

  const dropdown = computed(() =>
    agents.data?.map((o) => ({
      label: o.agent_name,
      value: o.name,
    }))
  );

  function searchAgents(query: string) {
    return agents.data.filter((a) =>
      a.user?.toLowerCase().includes(query.toLowerCase())
    );
  }

  return {
    dropdown,
    agents,
    searchAgents,
  };
});
