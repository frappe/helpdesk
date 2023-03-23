<template>
	<div class="leading-loose">
		<router-link :to="toRoute">
			<div class="truncate" :class="{ 'font-semibold': !isSeen }">
				{{ subject }}
			</div>
		</router-link>
		<div class="flex flex-wrap items-center gap-2">
			<div>&#x0023;</div>
			<div>{{ ticketName }}</div>
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
import { computed, defineProps, toRefs } from "vue";
import { FeatherIcon, createDocumentResource } from "frappe-ui";

const props = defineProps({
	ticketName: {
		type: String,
		required: true,
	},
});

const { ticketName } = toRefs(props);
const toRoute = computed(() => `tickets/${ticketName.value}`);
const subject = computed(() => ticket.doc?.subject);
const metaData = computed(() => ticket.getMeta?.data?.message);
const conversationCount = computed(() => metaData.value?.conversation_count);
const commentCount = computed(() => metaData.value?.comment_count);
const isSeen = computed(() => metaData.value?.is_seen);

const ticket = createDocumentResource({
	doctype: "Ticket",
	name: ticketName,
	cache: ["Ticket", ticketName],
	whitelistedMethods: {
		getMeta: {
			method: "get_meta",
			cache: ["TicketMetaData", ticketName],
		},
	},
});

ticket.getMeta.fetch();
</script>
