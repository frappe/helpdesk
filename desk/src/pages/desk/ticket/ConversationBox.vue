<template>
	<div class="flex flex-col overflow-hidden">
		<div
			v-if="isLoaded"
			ref="listElement"
			class="flex w-full flex-col items-center gap-4 overflow-auto"
		>
			<div class="content">
				<div v-for="(c, i) in conversations" :key="c.name" class="mt-4">
					<div v-if="isNewDay(i)">
						<div class="my-4 border-t text-center">
							<div class="-translate-y-1/2">
								<span class="bg-white px-2 text-xs text-gray-700">
									{{ dayShort(c.creation) }}
								</span>
							</div>
						</div>
					</div>
					<CommunicationItem
						v-if="c.isCommunication"
						:content="c.content"
						:date="c.creation"
						:sender="c.sender.full_name"
						:sender-image="c.sender.image"
						:cc="c.cc"
						:bcc="c.bcc"
						:attachments="c.attachments"
					>
						<template #extra="{ content, cc, bcc }">
							<Dropdown :options="dropdownOptions(content, cc, bcc)">
								<template #default>
									<FeatherIcon
										name="more-horizontal"
										class="h-5 w-5 cursor-pointer opacity-0 group-hover:opacity-100"
									/>
								</template>
							</Dropdown>
						</template>
					</CommunicationItem>
					<CommentItem
						v-else
						:name="c.name"
						:content="c.content"
						:date="c.creation"
						:sender="c.sender"
					/>
				</div>
			</div>
		</div>
		<div v-else class="flex grow items-center justify-center">
			<LoadingIndicator class="w-5 text-gray-900" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { useScroll } from "@vueuse/core";
import { debounce, Dropdown, FeatherIcon, LoadingIndicator } from "frappe-ui";
import dayjs from "dayjs";
import { orderBy, unionBy } from "lodash";
import { socket } from "@/socket";
import { useTicketStore } from "./data";
import CommunicationItem from "@/components/CommunicationItem.vue";
import CommentItem from "./CommentItem.vue";

type SocketData = {
	ticket_id: string;
};

const { editor, ticket } = useTicketStore();
const listElement = ref(null);
const isCommunicationsLoaded = ref(false);
const isCommentsLoaded = ref(false);
const isLoaded = computed(
	() => isCommunicationsLoaded.value && isCommentsLoaded.value
);

watch(isLoaded, (v) => {
	if (v) scrollBottom();
});
watch(
	() => editor.isExpanded,
	() => scrollBottom()
);

ticket.getCommunications
	.submit()
	.then(() => (isCommunicationsLoaded.value = true));
ticket.getComments.submit().then(() => (isCommentsLoaded.value = true));

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

function dropdownOptions(content: string, cc: string, bcc: string) {
	return [
		{
			label: "Reply",
			handler: () => {
				editor.cc = [];
				editor.bcc = [];
				editor.content = quote(content);
				editor.isExpanded = true;
			},
		},
		{
			label: "Reply All",
			handler: () => {
				editor.cc = cc.split(",");
				editor.bcc = bcc.split(",");
				editor.content = quote(content);
				editor.isExpanded = true;
			},
		},
	];
}

const scrollBottom = debounce(() => {
	const { y } = useScroll(listElement, { behavior: "smooth" });
	y.value = listElement.value.scrollHeight;
}, 500);

function mapCommunication(c) {
	return {
		...c,
		isCommunication: true,
	};
}

function isNewDay(index: number) {
	if (index === 0) return true;

	const currEntry = conversations.value[index];
	const prevEntry = conversations.value[index - 1];

	return dayjs(currEntry.creation).diff(prevEntry.creation, "day") > 0;
}

function dayShort(date: string) {
	switch (dayjs(date).diff(dayjs(), "day")) {
		case 0:
			return "Today";
		case 1:
			return "Yesterday";
		default:
			return dayjs(date).format("DD/MM/YYYY");
	}
}

function quote(s: string) {
	return `<blockquote>${s}</blockquote><br/>`;
}

socket.on("helpdesk:new-communication", (data: SocketData) => {
	if (data.ticket_id !== ticketId.value) return;
	ticket.getCommunications.reload().then(() => scrollBottom());
});

socket.on("helpdesk:new-ticket-comment", (data: SocketData) => {
	if (data.ticket_id !== ticketId.value) return;
	ticket.getComments.reload().then(() => scrollBottom());
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
