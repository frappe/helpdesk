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
import { defineProps, toRefs, ref, Ref } from "vue";
import { Avatar, createDocumentResource } from "frappe-ui";

type TicketAssignee = {
	full_name: string;
	user_image: string;
};

const props = defineProps({
	ticketId: {
		type: String,
		required: true,
	},
});

const { ticketId } = toRefs(props);
const avatarUrl: Ref<string> = ref(null);
const agentName: Ref<string> = ref(null);

const ticket = createDocumentResource({
	doctype: "Ticket",
	name: ticketId,
	cache: ["Ticket", ticketId],
	whitelistedMethods: {
		getAssignees: {
			method: "get_assignees",
			onSuccess: (data: Array<TicketAssignee>) => {
				const agent = data.pop();
				avatarUrl.value = agent?.user_image;
				agentName.value = agent?.full_name;
			},
		},
	},
});

ticket.getAssignees.fetch();
</script>
