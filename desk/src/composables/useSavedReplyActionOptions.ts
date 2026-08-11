import { type ActionOption } from "@/components/Settings/SavedReplies/components/actionTypes";
import { useTags, type Tag } from "@/composables/useTags";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { SavedReplyActionType } from "@/types";
import { useDebounceFn } from "@vueuse/core";
import { createListResource } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed } from "vue";

const SEARCH_PAGE_LENGTH = 10;

let shared: ReturnType<typeof buildActionOptions> | undefined;

/**
 * The pickable values for each saved reply action type. Shared so the settings
 * editor and the reply composer offer the same list instead of each building
 * its own. Built once: every action chip calls this, and a resource per caller
 * means a list request per chip.
 */
export function useSavedReplyActionOptions() {
  return (shared ??= buildActionOptions());
}

function buildActionOptions() {
  const statusStore = useTicketStatusStore();
  const priorityStore = useTicketPriorityStore();
  const agentStore = useAgentStore();
  const { tagListResource } = useTags();
  const { teamRestrictionApplied } = storeToRefs(useConfigStore());
  const { userTeams, isAdmin } = storeToRefs(useAuthStore());

  const ticketTypesResource = createListResource({
    doctype: "HD Ticket Type",
    cache: ["HD Ticket Type", "search"],
    fields: ["name"],
    filters: { disabled: 0 },
    pageLength: SEARCH_PAGE_LENGTH,
    auto: true,
  });

  const teamsResource = createListResource({
    doctype: "HD Team",
    cache: ["HD Team", "search"],
    fields: ["name"],
    filters: { disabled: 0 },
    pageLength: SEARCH_PAGE_LENGTH,
    auto: true,
  });

  /** Link fields: these lists are fetched by query instead of held whole. */
  const searchResources: Partial<
    Record<SavedReplyActionType, ReturnType<typeof createListResource>>
  > = {
    "Set Ticket Type": ticketTypesResource,
    "Set Team": teamsResource,
  };

  const search = useDebounceFn((type: SavedReplyActionType, query: string) => {
    const resource = searchResources[type];
    if (!resource) return;
    resource.update({
      filters: { ...resource.filters, name: ["like", `%${query}%`] },
    });
    resource.reload();
  }, 300);

  // A restricted agent can only route to their own teams
  const teamOptions = computed<ActionOption[]>(() => {
    const names =
      !isAdmin.value && teamRestrictionApplied.value
        ? userTeams.value || []
        : (teamsResource.data || []).map((team: { name: string }) => team.name);
    return names.map((name: string) => ({ label: name, value: name }));
  });

  /** Tags as a plain list; callers filter it further if they need to. */
  function tagOptions(): ActionOption[] {
    return ((tagListResource.data || []) as Tag[]).map((tag) => ({
      label: tag.name,
      value: tag.name,
      color: tag.color,
    }));
  }

  function valueOptions(type: SavedReplyActionType): ActionOption[] {
    switch (type) {
      case "Set Status":
        return (statusStore.statuses.data || [])
          .filter((status) => status.enabled)
          .map((status) => ({
            label: status.label_agent,
            value: status.label_agent,
          }));
      case "Set Priority":
        return (priorityStore.priorities.data || [])
          .filter((priority) => !priority.disabled)
          .map((priority) => ({ label: priority.name, value: priority.name }));
      case "Set Team":
        return teamOptions.value;
      case "Set Ticket Type":
        return (ticketTypesResource.data || []).map(
          (ticketType: { name: string }) => ({
            label: ticketType.name,
            value: ticketType.name,
          })
        );
      case "Assign Agent":
        return agentStore.dropdown || [];
      case "Add Tag":
      case "Remove Tag":
        return tagOptions();
      default:
        return [];
    }
  }

  if (!agentStore.agents.data) agentStore.agents.fetch();

  return { valueOptions, tagOptions, search };
}
