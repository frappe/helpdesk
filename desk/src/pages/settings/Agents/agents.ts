import { isCustomerPortal } from "@/utils";
import { createListResource, createResource } from "frappe-ui";
import { reactive, ref, watch } from "vue";

const PAGE_LENGTH = 20;

export const agents = createListResource({
  doctype: "HD Agent",
  fields: ["name", "user_image", "agent_name", "is_active"],
  start: 0,
  pageLength: PAGE_LENGTH,
  orderBy: "creation desc",
  auto: !isCustomerPortal.value,
});

export const activeFilter = ref("Active");
export const showNewAgentsDialog = ref(false);

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
      agents.pageLength = PAGE_LENGTH;
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
      agents.pageLength = PAGE_LENGTH;
      agents.reload();
    },
    { deep: true }
  );
  watch(
    activeFilter,
    (newVal) => {
      if (newVal === "Active") {
        agents.filters = {
          ...agents.filters,
          is_active: 1,
        };
      } else if (newVal === "Inactive") {
        agents.filters = {
          ...agents.filters,
          is_active: 0,
        };
      } else {
        agents.filters = {
          ...agents.filters,
          is_active: ["in", [0, 1]],
        };
      }
      agents.start = 0;
      agents.pageLength = PAGE_LENGTH;
      agents.reload();
    },
    { immediate: true }
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
