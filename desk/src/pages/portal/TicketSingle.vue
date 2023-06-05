<template>
	<div class="px-9 py-4 text-base text-gray-900">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-2 py-4">
				<RouterLink :to="{ name: CUSTOMER_PORTAL_LANDING }">
					<IconCaretLeft class="h-4 w-4 cursor-pointer text-gray-700" />
				</RouterLink>
				<div class="line-clamp-1 text-xl font-medium text-gray-900">
					{{ ticket.doc?.subject }}
				</div>
				<div class="flex items-center gap-2 text-xs font-normal text-gray-700">
					<IconHash class="h-3 w-3" />
					{{ ticket.doc?.name }}
				</div>
			</div>
			<span v-if="ticket.doc?.status !== 'Closed'">
				<Button
					v-if="ticket.doc?.status == 'Resolved'"
					label="Reopen"
					icon-left="repeat"
					class="bg-gray-900 text-white hover:bg-gray-800"
					@click="ticket.reopen.submit()"
				/>
				<Button
					v-else
					label="Mark as resolved"
					icon-left="check"
					class="bg-gray-900 text-white hover:bg-gray-800"
					@click="ticket.resolve.submit()"
				/>
			</span>
		</div>
		<div class="flex flex-col gap-6">
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
		</div>
		<TextEditor
			ref="textEditor"
			class="mt-6"
			:placeholder="placeholder"
			:content="editorContent"
			:attachments="attachments"
			@change="(v) => (editorContent = v)"
			@attachment-added="(item) => attachments.add(item)"
			@attachment-removed="(item) => attachments.delete(item)"
		>
			<template #bottom="{ editor }">
				<TextEditorBottom :editor="editor">
					<template #actions-right>
						<Button
							label="Send"
							class="bg-gray-900 text-white hover:bg-gray-800"
							:disabled="editor.isEmpty"
							@click="newCommunication"
						/>
					</template>
				</TextEditorBottom>
			</template>
		</TextEditor>
	</div>
</template>

<script setup lang="ts">
import { Ref, onMounted, onUnmounted, ref } from "vue";
import { createDocumentResource, debounce } from "frappe-ui";
import dayjs from "dayjs";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import { socket } from "@/socket";
import { useConfigStore } from "@/stores/config";
import CommunicationItem from "@/components/CommunicationItem.vue";
import TextEditor from "@/components/text-editor/TextEditor.vue";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";
import IconCaretLeft from "~icons/ph/caret-left";
import IconHash from "~icons/espresso/hash";

const props = defineProps({
	ticketId: {
		type: String,
		required: true,
	},
});

const configStore = useConfigStore();
const ticket = createDocumentResource({
	doctype: "HD Ticket",
	name: props.ticketId,
	auto: true,
	onSuccess() {
		configStore.setTitle(ticket.doc?.subject);
	},
	whitelistedMethods: {
		getCommunications: {
			method: "get_communications",
			auto: true,
		},
		newCommunication: {
			method: "create_communication_via_contact",
			onSuccess() {
				clearEditor();
			},
		},
		reopen: "reopen",
		resolve: "resolve",
	},
});

const textEditor = ref(null);
const placeholder = "Type a message";
const editorContent = ref("");
const attachments: Ref<Set<Record<any, any>>> = ref(new Set([]));

const newCommunication = debounce(() => {
	const message = editorContent.value;
	const attachmentNames = Array.from(attachments.value).map((a) => a.name);

	ticket.newCommunication.submit({
		message,
		attachments: attachmentNames,
	});
}, 500);

function clearEditor() {
	textEditor.value?.editor.commands.clearContent();
	attachments.value.clear();
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
	configStore.setTitle();
	socket.off("helpdesk:new-communication");
});
</script>
