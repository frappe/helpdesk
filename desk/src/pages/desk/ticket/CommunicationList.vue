<template>
	<div class="flex flex-col items-center overflow-scroll">
		<div class="content flex flex-col gap-4">
			<span v-for="c in conversations" :key="c.name">
				<CommunicationItem
					v-if="c.isCommunication"
					:content="c.content"
					:date="c.creation"
					:sender="c.sender.full_name"
					:sender-image="c.sender.image"
					:cc="c.cc"
					:bcc="c.bcc"
					:attachments="c.attachments"
				/>
				<CommentItem
					v-else
					:name="c.name"
					:content="c.content"
					:date="c.creation"
					:sender="c.sender"
				/>
			</span>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import dayjs from "dayjs";
import { ticket } from "./data";
import { socket } from "@/socket";
import CommentItem from "./CommentItem.vue";
import CommunicationItem from "./CommunicationItem.vue";

type SocketData = {
	ticket_id: string;
};

ticket.getCommunications.submit();
ticket.getComments.submit();

const ticketId = computed(() => ticket.doc.name);
const communications = computed(
	() =>
		ticket.getCommunications.data?.message?.map((c) => ({
			...c,
			isCommunication: true,
		})) || []
);
const comments = computed(
	() =>
		ticket.getComments.data?.message?.map((c) => ({
			...c,
			isComment: true,
		})) || []
);
const conversations = computed(() =>
	[...communications.value, ...comments.value].sort((a, b) =>
		dayjs(a.creation).diff(b.creation)
	)
);

function execOnSocketEvent(data: SocketData, callback: () => void) {
	if (parseInt(data.ticket_id) === ticketId.value) callback();
}

socket.on("helpdesk:new-communication", (data: SocketData) =>
	execOnSocketEvent(data, ticket.getCommunications.reload)
);
socket.on("helpdesk:new-ticket-comment", (data: SocketData) =>
	execOnSocketEvent(data, ticket.getComments.reload)
);
socket.on("helpdesk:delete-ticket-comment", (data: SocketData) =>
	execOnSocketEvent(data, ticket.getComments.reload)
);
</script>

<style scoped>
.content {
	width: 742px;
}
</style>
