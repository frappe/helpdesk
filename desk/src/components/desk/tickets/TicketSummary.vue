<template>
	<div class="leading-relaxed">
		<router-link :to="toRoute">
			<div
				class="line-clamp-2 text-gray-700"
				:class="{ 'font-semibold': !isSeen }"
			>
				{{ subject }}
			</div>
		</router-link>
		<div class="flex flex-wrap items-center gap-2 text-gray-600">
			<IconHash class="h-4 w-4" />
			<div>{{ ticketName }}</div>
			<IconDot class="h-4 w-4" />
			<IconMail class="h-4 w-4" />
			{{ conversationCount }}
			<IconDot class="h-4 w-4" />
			<IconComment class="h-4 w-4" />
			{{ commentCount }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, toRefs } from "vue";
import { createDocumentResource } from "frappe-ui";
import IconDot from "~icons/ph/dot-outline-fill";
import IconHash from "~icons/espresso/hash";
import IconMail from "~icons/espresso/mail";
import IconComment from "~icons/espresso/comment";

const props = defineProps({
	ticketName: {
		type: String,
		required: true,
	},
});

const { ticketName } = toRefs(props);
const toRoute = computed(() => ({
	name: "DeskTicket",
	params: {
		ticketId: ticketName.value,
	},
}));
const subject = computed(() => ticket.doc?.subject);
const metaData = computed(() => ticket.getMeta?.data?.message);
const conversationCount = computed(() => metaData.value?.conversation_count);
const commentCount = computed(() => metaData.value?.comment_count);
const isSeen = computed(() => metaData.value?.is_seen);

const ticket = createDocumentResource({
	doctype: "HD Ticket",
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
