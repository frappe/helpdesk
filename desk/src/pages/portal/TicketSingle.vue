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
		<span>
			<div
				class="mt-6 flex items-start gap-2.5 rounded-xl border border-gray-300"
			>
				<TextEditor
					v-if="isEditorExpanded"
					ref="editor"
					:bubble-menu="true"
					:floating-menu="true"
					:content="editorContent"
					:placeholder="placeholder"
					editor-class="prose-sm max-w-none p-3 overflow-auto h-32 focus:outline-none"
					@change="(v) => (editorContent = v)"
				>
					<template #bottom>
						<div class="flex flex-wrap gap-2 px-2">
							<AttachmentItem
								v-for="attachment in attachments"
								:key="attachment.file_name"
								:label="attachment.file_name"
								class="w-max"
							>
								<template #extra>
									<IconX
										class="h-4 w-4 cursor-pointer"
										@click="attachments.delete(attachment)"
									/>
								</template>
							</AttachmentItem>
						</div>
						<div class="flex items-center justify-between p-2">
							<FileUploader @success="(file) => attachments.add(file)">
								<template #default="{ uploading, openFileSelector }">
									<div class="flex h-7 w-7 items-center justify-center">
										<IconAttachment
											class="h-5 w-5 cursor-pointer text-gray-900"
											:class="{
												'text-gray-600': uploading,
											}"
											@click="!uploading && openFileSelector()"
										/>
									</div>
								</template>
							</FileUploader>
							<div class="flex items-center gap-4">
								<IconDelete
									class="h-5 w-5 cursor-pointer"
									@click="clearEditor"
								/>
								<Button
									label="Reply"
									class="bg-gray-900 text-white hover:bg-gray-800"
									:disabled="editor?.editor.isEmpty"
									@click="newCommunication"
								/>
							</div>
						</div>
					</template>
				</TextEditor>
				<div
					v-else
					class="flex h-8 w-full cursor-pointer select-none items-center rounded px-2.5 text-base text-gray-500"
					@click="isEditorExpanded = true"
				>
					{{ placeholder }}
				</div>
			</div>
		</span>
	</div>
</template>

<script setup lang="ts">
import { Ref, onMounted, onUnmounted, ref, watch } from "vue";
import { createDocumentResource, FileUploader, TextEditor } from "frappe-ui";
import dayjs from "dayjs";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import { socket } from "@/socket";
import AttachmentItem from "@/components/AttachmentItem.vue";
import CommunicationItem from "@/components/CommunicationItem.vue";
import IconHash from "~icons/espresso/hash";
import IconHome from "~icons/espresso/home";
import IconRightChevron from "~icons/espresso/right-chevron";
import IconAttachment from "~icons/espresso/attachment";
import IconDelete from "~icons/espresso/delete";
import IconX from "~icons/ph/x";

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
		newCommunication: {
			method: "create_communication_via_contact",
			onSuccess() {
				clearEditor();
			},
		},
	},
});

const editor = ref(null);
const placeholder = "Type a reply";
const isEditorExpanded = ref(false);
const editorContent = ref("");
const attachments: Ref<Set<Record<any, any>>> = ref(new Set([]));
watch(editor, (e) => e?.editor.commands.focus());

function newCommunication() {
	const message = editorContent.value;
	const attachmentNames = Array.from(attachments.value).map((a) => a.name);

	ticket.newCommunication.submit({
		message,
		attachments: attachmentNames,
	});
}

function clearEditor() {
	editorContent.value = "";
	isEditorExpanded.value = false;
	attachments.value.clear();
}

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
