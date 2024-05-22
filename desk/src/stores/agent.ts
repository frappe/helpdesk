import { computed } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

export const useAgentStore = defineStore("agent", () => {
  const agents = createListResource({
    doctype: "HD Agent",
    fields: ["name", "agent_name", "is_active", "user", "user.user_image"],
    auto: true,
    pageLength: 99999,
  });

  const dropdown = computed(() =>
    agents.data?.map((o) => ({
      label: o.agent_name,
      value: o.name,
    }))
  );

  return {
    dropdown,
    agents,
  };
});
