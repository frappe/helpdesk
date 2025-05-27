import { createListResource, createResource } from "frappe-ui";
import { reactive, ref, watch } from "vue";

export const agents = createListResource({
  doctype: "HD Agent",
  fields: ["name", "user_image", "agent_name", "is_active"],
  cache: ["hd_agent_list"],
  start: 0,
  pageLength: 10,
  orderBy: "modified desc",
  auto: true,
});

export const useAgents = () => {
  const search = ref("");
  const filters = reactive({});
  watch(search, (newValue) => {
    agents.filters = {
      agent_name: ["like", `%${newValue}%`],
      ...filters,
    };
    if (!newValue) {
      agents.filters = {
        ...filters,
      };
      agents.start = 0;
      agents.pageLength = 10;
    }
    agents.reload();
  });
  watch(
    filters,
    (newVal) => {
      agents.filters = {
        ...agents.filters,
        ...newVal,
      };
      agents.start = 0;
      agents.pageLength = 10;
      agents.reload();
    },
    { deep: true }
  );

  async function updateAgent(agent: string, isActive: boolean | number) {
    const res = createResource({
      url: "frappe.client.set_value",
      params: {
        doctype: "HD Agent",
        name: agent,
        fieldname: "is_active",
        value: isActive,
      },
    });
    await res.submit();
  }

  return {
    search,
    agents,
    filters,
    updateAgent,
  };
};

export const showNewAgentsDialog = ref(false);
