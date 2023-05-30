<template>
	<div class="px-9 py-4 text-base text-gray-900">
		<div class="mb-4 flex items-center gap-2 text-gray-700">
			<IconHome
				class="h-4 w-4 cursor-pointer hover:text-gray-900"
				@click="goHome"
			/>
			<IconRightChevron class="h-4 w-4" />
			<RouterLink
				:to="{ name: CUSTOMER_PORTAL_LANDING }"
				class="cursor-pointer hover:text-gray-900"
			>
				My tickets
			</RouterLink>
			<IconRightChevron class="h-4 w-4" />
			<IconHash class="h-3 w-3" />
			{{ ticket.doc?.name }}
		</div>
		<div class="mb-8 text-xl font-medium">
			{{ ticket.doc?.subject }}
		</div>
		<span>
			<div
				v-for="(communication, index) in ticket.getCommunications.data?.message"
				:key="communication.name"
			>
				<div v-if="isNewDay(index)">
					<div class="my-4 border-t text-center">
						<div class="-translate-y-1/2">
							<span class="bg-white px-2 text-xs text-gray-700">
								{{ dayShort(communication.creation) }}
							</span>
						</div>
					</div>
				</div>
				<CommunicationItem
					:content="communication.content"
					:date="communication.creation"
					:sender="communication.sender.full_name"
					:sender-image="communication.sender.image"
					:cc="communication.cc"
					:bcc="communication.bcc"
					:attachments="communication.attachments"
				/>
			</div>
		</span>
	</div>
</template>

<script setup lang="ts">
import { createDocumentResource } from "frappe-ui";
import dayjs from "dayjs";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import { socket } from "@/socket";
import CommunicationItem from "@/components/CommunicationItem.vue";
import IconHash from "~icons/espresso/hash";
import IconHome from "~icons/espresso/home";
import IconRightChevron from "~icons/espresso/right-chevron";
import { onMounted, onUnmounted } from "vue";

const props = defineProps({
	ticketId: {
		type: String,
		required: true,
	},
});

const ticket = createDocumentResource({
	doctype: "HD Ticket",
	name: props.ticketId,
	auto: true,
	whitelistedMethods: {
		getCommunications: {
			method: "get_communications",
			auto: true,
		},
	},
});

function goHome() {
	const protocol = window.location.protocol;
	const domain = window.location.hostname;
	const path = protocol + "//" + domain;

	window.location.href = path;
}

function isNewDay(index: number) {
	if (index === 0) return true;
	const conversations = ticket.getCommunications.data?.message;

	const currEntry = conversations[index];
	const prevEntry = conversations[index - 1];

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

onMounted(() => {
	socket.on("helpdesk:new-communication", (data) => {
		if (data.ticket_id === parseInt(props.ticketId))
			ticket.getCommunications.reload();
	});
});

onUnmounted(() => {
	socket.off("helpdesk:new-communication");
});
</script>
