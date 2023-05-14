<template>
	<div class="flex flex-col justify-between">
		<router-link :to="toRoute">
			<div class="flex justify-between">
				<div
					class="line-clamp-1"
					:class="{
						'text-gray-700': isSeen,
						'text-gray-900': !isSeen,
					}"
				>
					{{ subject }}
				</div>
				<div
					v-if="!isSeen"
					class="badge-new mr-2 flex items-center justify-center bg-gray-900 text-xs text-white"
				>
					New
				</div>
			</div>
		</router-link>
		<div class="flex flex-wrap items-center gap-2 text-xs text-gray-600">
			<IconHash class="h-3 w-3" />
			<div>{{ ticketName }}</div>
			<IconDot class="h-3 w-3" />
			<IconMail class="h-3 w-3" />
			{{ conversationCount }}
			<IconDot class="h-3 w-3" />
			<IconComment class="h-3 w-3" />
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

<style scoped>
.badge-new {
	padding: 3px 6px;
	width: 38px;
	height: 20px;
	border-radius: 5px;
}
</style>
