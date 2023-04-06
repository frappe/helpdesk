<template>
	<div class="flex items-center gap-2">
		<div class="">
			<Avatar size="sm" :label="agentName" :image-u-r-l="avatarUrl" />
		</div>
		<div class="truncate">
			{{ agentName }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, defineProps, toRefs } from "vue";
import { Avatar, createDocumentResource } from "frappe-ui";

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
</script>
