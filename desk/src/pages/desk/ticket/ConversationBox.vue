<template>
	<div
		ref="listElement"
		class="mt-8 flex flex-col items-center overflow-scroll"
	>
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
import { computed, onUnmounted, ref, watch } from "vue";
import { useScroll } from "@vueuse/core";
import dayjs from "dayjs";
import { orderBy, unionBy } from "lodash";
import { socket } from "@/socket";
import { ticket } from "./data";
import CommentItem from "./CommentItem.vue";
import CommunicationItem from "./CommunicationItem.vue";

type SocketData = {
	ticket_id: string;
};

ticket.getCommunications
	.submit()
	.then(() => (isCommunicationsLoaded.value = true));
ticket.getComments.submit().then(() => (isCommentsLoaded.value = true));

const listElement = ref<HTMLElement | null>(null);
const { y: scrollY } = useScroll(listElement, { behavior: "smooth" });

const isCommunicationsLoaded = ref(false);
const isCommentsLoaded = ref(false);
const isLoaded = computed(
	() => isCommunicationsLoaded.value && isCommentsLoaded.value
);

watch(isLoaded, (v) => {
	if (v) scrollToBottom();
});

const ticketId = computed(() => ticket.doc.name);
const communications = computed(
	() => ticket.getCommunications.data?.message?.map(mapCommunication) || []
);
const comments = computed(() => ticket.getComments.data?.message || []);
const conversations = computed(() =>
	orderBy(unionBy(communications.value, comments.value), (c) =>
		dayjs(c.creation)
	)
);

function mapCommunication(c) {
	return {
		...c,
		isCommunication: true,
	};
}

function scrollToBottom() {
	scrollY.value = listElement.value.scrollHeight;
}

socket.on("helpdesk:new-communication", (data: SocketData) => {
	if (data.ticket_id !== ticketId.value) return;
	ticket.getCommunications.reload().then(() => scrollToBottom());
});

socket.on("helpdesk:new-ticket-comment", (data: SocketData) => {
	if (data.ticket_id !== ticketId.value) return;
	ticket.getComments.reload().then(() => scrollToBottom());
});

socket.on("helpdesk:delete-ticket-comment", (data: SocketData) => {
	if (data.ticket_id !== ticketId.value) return;
	ticket.getComments.reload();
});

onUnmounted(() => {
	socket.off("helpdesk:new-communication");
	socket.off("helpdesk:new-ticket-comment");
	socket.off("helpdesk:delete-ticket-comment");
});
</script>

<style scoped>
.content {
	width: 742px;
}
</style>
