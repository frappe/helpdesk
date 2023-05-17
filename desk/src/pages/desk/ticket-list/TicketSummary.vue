<template>
	<router-link
		:to="toRoute"
		class="flex justify-between"
		:class="{
			'text-gray-700': isSeen,
			'text-gray-900': !isSeen,
		}"
	>
		<div class="line-clamp-1">
			{{ subject }}
		</div>
		<div class="mr-2 flex items-center gap-1">
			<Tooltip v-if="!isSeen" text="New ticket">
				<span class="relative flex h-3 w-3 items-center justify-center">
					<span
						class="absolute inline-flex h-full w-full animate-ping rounded-full bg-gray-500 opacity-75"
					></span>
					<div class="h-1.5 w-1.5 rounded-full bg-gray-800"></div>
				</span>
			</Tooltip>
			<div class="flex items-center gap-1">
				<IconHash class="h-3 w-3" />
				{{ ticketName }}
			</div>
		</div>
	</router-link>
	<!-- <div class="flex flex-wrap items-center gap-2 text-xs text-gray-600"> -->
	<!-- 	<IconHash class="h-3 w-3" /> -->
	<!-- 	<div>{{ ticketName }}</div> -->
	<!-- 	<IconDot class="h-3 w-3" /> -->
	<!-- 	<IconMail class="h-3 w-3" /> -->
	<!-- 	{{ conversationCount }} -->
	<!-- 	<IconDot class="h-3 w-3" /> -->
	<!-- 	<IconComment class="h-3 w-3" /> -->
	<!-- 	{{ commentCount }} -->
	<!-- </div> -->
</template>

<script setup lang="ts">
import { computed, toRefs } from "vue";
import { createDocumentResource, Tooltip } from "frappe-ui";
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
// const isSeen = computed(() => metaData.value?.is_seen);

const isSeen = Math.random() < 0.5;

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

<style scoped>
.badge-new {
	padding: 3px 6px;
	width: 38px;
	height: 20px;
	border-radius: 5px;
}
</style>
