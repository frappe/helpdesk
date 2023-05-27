<template>
	<Tooltip :text="getTooltipLabel(agentName)">
		<Avatar size="sm" :label="agentName" :image-u-r-l="avatarUrl" />
	</Tooltip>
</template>

<script setup lang="ts">
import { computed, defineProps, toRefs } from "vue";
import { createDocumentResource, Avatar, Tooltip } from "frappe-ui";

const props = defineProps({
	ticketId: {
		type: String,
		required: true,
	},
});

const { ticketId } = toRefs(props);
const assignees = computed(() => ticket.getAssignees?.data?.message || []);
const assignee = computed(() => [...assignees.value].pop());
const agentName = computed(() => assignee.value?.full_name);
const avatarUrl = computed(() => assignee.value?.user_image);

const ticket = createDocumentResource({
	doctype: "HD Ticket",
	name: ticketId,
	cache: ["Ticket", ticketId],
	whitelistedMethods: {
		getAssignees: {
			method: "get_assignees",
			cache: ["TicketAssignees", ticketId],
		},
	},
});

ticket.getAssignees.fetch();

function getTooltipLabel(s: string) {
	return "Assigned to " + s;
}
</script>
