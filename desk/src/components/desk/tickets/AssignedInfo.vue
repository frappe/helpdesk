<template>
	<div>
		<div class="inline-block align-middle">
			<Avatar size="sm" :label="agentName" :image-u-r-l="avatarUrl" />
		</div>
		<div class="ml-2 inline-block truncate align-middle">
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
const assignees = computed(() => ticket.getAssignees?.data?.message?.pop());
const agentName = computed(() => assignees.value?.full_name);
const avatarUrl = computed(() => assignees.value?.user_image);

const ticket = createDocumentResource({
	doctype: "Ticket",
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
