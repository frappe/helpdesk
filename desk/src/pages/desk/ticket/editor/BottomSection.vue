<template>
	<div>
		<div class="flex flex-col divide-y rounded-b-xl">
			<div class="ml-2 flex flex-wrap gap-2 py-2">
				<AttachmentItem
					v-for="attachment in editor.attachments"
					:key="attachment"
					:label="attachment.file_name"
				>
					<template #extra>
						<IconX
							class="h-4 w-4 cursor-pointer"
							@click="removeAttachment(attachment.name)"
						/>
					</template>
				</AttachmentItem>
			</div>
			<div v-if="isTextFormattingVisible" class="px-3.5 py-2">
				<TextEditorFixedMenu :buttons="menuButtons" />
			</div>
			<div class="flex justify-between px-3.5 py-2">
				<div class="flex flex-row items-center space-x-2">
					<CustomIcons
						:class="{
							'bg-gray-200': isTextFormattingVisible,
						}"
						name="text-formatting"
						class="h-7 w-7 rounded p-1"
						role="button"
						@click="isTextFormattingVisible = !isTextFormattingVisible"
					/>
					<FileUploader @success="(file) => editor.attachments.push(file)">
						<template #default="{ uploading, openFileSelector }">
							<FeatherIcon
								name="paperclip"
								class="h-5 w-5"
								role="button"
								:disabled="uploading"
								@click="openFileSelector"
							/>
						</template>
					</FileUploader>
					<CustomIcons
						name="add-response"
						class="h-7 w-7 rounded p-1"
						role="button"
						@click="showCannedResponses = true"
					/>
					<CustomIcons
						name="article-reply"
						class="h-7 w-7 rounded p-1"
						role="button"
						@click="showArticleResponse = true"
					/>
				</div>
				<div class="flex items-center gap-4">
					<IconDelete
						class="h-5 w-5 cursor-pointer text-gray-900"
						@click.prevent="clean"
					/>
					<div class="flex">
						<Button
							label="Reply"
							appearance="primary"
							class="rounded-r-none"
							@click="newCommunication"
						/>
						<Dropdown
							:options="dropdownOptions"
							:button="{
								icon: 'chevron-down',
								appearance: 'primary',
								class: 'rounded-l-none',
							}"
						/>
					</div>
				</div>
			</div>
		</div>
		<ArticleResponses
			:show="showArticleResponse"
			@close="showArticleResponse = false"
			@contentVal="(val) => (editor.content = val)"
		/>
		<CannedResponses
			:show="showCannedResponses"
			@close="showCannedResponses = false"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import {
	createResource,
	Button,
	Dropdown,
	FeatherIcon,
	FileUploader,
	TextEditorFixedMenu,
} from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { editor, ticket, clean } from "../data";
import { TextEditorMenuButtons as menuButtons } from "../../consts";
import CannedResponses from "./CannedResponses.vue";
import ArticleResponses from "./ArticleResponses.vue";
import AttachmentItem from "@/components/AttachmentItem.vue";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";
import IconDelete from "~icons/espresso/delete";
import IconX from "~icons/ph/x";

const authStore = useAuthStore();
const showArticleResponse = ref(false);
const showCannedResponses = ref(false);
const isTextFormattingVisible = ref(false);
const dropdownOptions = [
	{
		label: "Reply",
		handler: () => newCommunication(),
	},
	{
		label: "Comment",
		handler: () => newComment(),
	},
];

const insertRes = createResource({
	url: "frappe.client.insert",
	onSuccess() {
		clean();
	},
});

function removeAttachment(name: string) {
	editor.attachments = editor.attachments.filter((x) => x.name != name);
}

function newCommunication() {
	ticket.replyViaAgent.submit({
		attachments: editor.attachments.map((x) => x.name),
		cc: editor.cc.join(","),
		bcc: editor.bcc.join(","),
		message: editor.content,
	});
}

function newComment() {
	insertRes.submit({
		doc: {
			doctype: "HD Ticket Comment",
			reference_ticket: ticket.doc.name,
			content: editor.content,
			commented_by: authStore.userId,
		},
	});
}
</script>
