<template>
	<div class="leading-loose">
		<div class="truncate" :class="{ 'font-semibold': !isSeen }">
			{{ subject }}
		</div>
		<div class="flex flex-wrap items-center gap-2">
			<div>&#x0023;</div>
			<div>{{ name }}</div>
			<div>&#x2022;</div>
			<FeatherIcon name="message-circle" class="h-4 w-4" />
			{{ commentCount }}
			<div>&#x2022;</div>
			<FeatherIcon name="mail" class="h-4 w-4" />
			{{ conversationCount }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { defineProps, ref, toRefs } from "vue";
import { FeatherIcon, createDocumentResource } from "frappe-ui";

type TicketMetaData = {
	comment_count: number;
	conversation_count: number;
	is_seen: boolean;
};

const props = defineProps({
	ticketName: {
		type: String,
		required: true,
	},
});

const { ticketName } = toRefs(props);
const subject = ref("");
const name = ref("");
const conversationCount = ref(0);
const commentCount = ref(0);
const isSeen = ref(true);

const ticket = createDocumentResource({
	doctype: "Ticket",
	name: ticketName,
	cache: ["Ticket", ticketName],
	whitelistedMethods: {
		getMeta: {
			method: "get_meta",
			cache: ["TicketMetaData", ticketName],
			onSuccess: (data: TicketMetaData) => {
				conversationCount.value = data.conversation_count;
				commentCount.value = data.comment_count;
				isSeen.value = data.is_seen;
			},
		},
	},
	onSuccess: (data) => {
		ticket.getMeta.fetch();
		subject.value = data.subject;
		name.value = data.name;
	},
	auto: true,
});
</script>
