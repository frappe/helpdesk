<template>
	<div class="leading-relaxed">
		<router-link :to="toRoute">
			<div class="line-clamp-2" :class="{ 'font-semibold': !isSeen }">
				{{ subject }}
			</div>
		</router-link>
		<div class="flex flex-wrap items-center gap-2">
			<IconHash />
			<div>{{ ticketName }}</div>
			<div>&#x2022;</div>
			<IconMail />
			{{ conversationCount }}
			<div>&#x2022;</div>
			<IconComment />
			{{ commentCount }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, defineProps, toRefs } from "vue";
import { createDocumentResource } from "frappe-ui";
import IconHash from "@/assets/icons/hash.svg?component";
import IconMail from "@/assets/icons/mail.svg?component";
import IconComment from "@/assets/icons/comment.svg?component";

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
