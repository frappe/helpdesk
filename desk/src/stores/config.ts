import { socket } from "@/socket";
import { createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ComputedRef } from "vue";

export const useConfigStore = defineStore("config", () => {
  const configRes = createResource({
    url: "helpdesk.api.config.get_config",
    auto: true,
  });

  const config = computed(() => configRes.data || {});
  const brandLogo = computed(() => config.value.brand_logo);
  const teamRestrictionApplied = computed(
    () => !!parseInt(config.value.restrict_tickets_by_agent_group)
  );
  const assignWithinTeam = computed(
    () => !!parseInt(config.value.assign_within_team)
  );
  const skipEmailWorkflow: ComputedRef<boolean> = computed(
    () => !!parseInt(config.value.skip_email_workflow)
  );
  const preferKnowledgeBase = computed(
    () => !!parseInt(config.value.prefer_knowledge_base)
  );
  const isFeedbackMandatory = computed(
    () => !!parseInt(config.value.is_feedback_mandatory)
  );

  socket.on("helpdesk:settings-updated", () => configRes.reload());

  return {
    brandLogo,
    config,
    preferKnowledgeBase,
    skipEmailWorkflow,
    isFeedbackMandatory,
    teamRestrictionApplied,
    assignWithinTeam,
  };
});
