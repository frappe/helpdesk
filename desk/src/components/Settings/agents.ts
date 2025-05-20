import { createListResource } from "frappe-ui";
import { Ref, watch } from "vue";

const agents = createListResource({
  doctype: "HD Agent",
  fields: ["name", "user_image", "agent_name"],
  cache: ["hd_agent_list"],
  filters: {
    is_active: ["=", 1],
  },
  start: 0,
  pageLength: 10,
  orderBy: "creation desc",
  auto: true,
});

export const useAgents = (
  search: Ref<string>,
  filters: Record<string, unknown> = {}
) => {
  watch(search, (newValue) => {
    agents.filters = {
      is_active: ["=", 1],
      agent_name: ["like", `%${newValue}%`],
      ...filters,
    };
    if (!newValue) {
      agents.filters = {
        is_active: ["=", 1],
        ...filters,
      };
      agents.start = 0;
      agents.pageLength = 10;
    }
    agents.reload();
  });
  return {
    agents,
  };
};
