<template>
	<span>
		<TextEditorBottom
			:editor="editor.tiptap"
			:attachments="editor.attachments"
			@attachment-added="(item) => editor.attachments.push(item)"
			@attachment-removed="(item) => removeAttachment(item)"
		>
			<template #actions-left>
				<div class="flex h-7 w-7 items-center justify-center">
					<IconChat
						class="h-5 w-5 cursor-pointer text-gray-900"
						@click="showCannedResponses = true"
					/>
				</div>
				<div class="flex h-7 w-7 items-center justify-center">
					<IconKnowledgeBase
						class="h-5 w-5 cursor-pointer text-gray-900"
						@click="showArticleResponse = true"
					/>
				</div>
			</template>
			<template #actions-right>
				<div class="flex">
					<Button
						label="Reply"
						appearance="primary"
						class="rounded-r-none bg-gray-900 text-white hover:bg-gray-800"
						:disabled="isDisabled"
						@click="newCommunication"
					/>
					<Dropdown :options="dropdownOptions">
						<template #default="{ open }">
							<Button
								:icon="open ? 'chevron-up' : 'chevron-down'"
								appearance="primary"
								class="cursor-pointer rounded-l-none bg-gray-900 text-white hover:bg-gray-800"
								:disabled="isDisabled"
							/>
						</template>
					</Dropdown>
				</div>
			</template>
		</TextEditorBottom>
		<ArticleResponses
			:show="showArticleResponse"
			@close="showArticleResponse = false"
			@contentVal="(val) => (editor.content = val)"
		/>
		<CannedResponses
			:show="showCannedResponses"
			@close="showCannedResponses = false"
		/>
	</span>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { createResource, Button, Dropdown } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";
import { useTicketStore } from "../data";
import CannedResponses from "./CannedResponses.vue";
import ArticleResponses from "./ArticleResponses.vue";
import IconKnowledgeBase from "~icons/espresso/knowledge-base";
import IconChat from "~icons/espresso/chat";
import { createToast } from "@/utils/toasts";

const authStore = useAuthStore();
const { clean, editor, ticket } = useTicketStore();
const showArticleResponse = ref(false);
const showCannedResponses = ref(false);
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
	debounce: 500,
	onSuccess() {
		clean();
	},
	validate() {
		if (editor.tiptap?.isEmpty) {
			return "Message is empty";
		}
	},
	onError(error) {
		createToast({
			title: error.message,
			text: error.messages?.join("\n"),
			icon: "x",
			iconClasses: "text-red-500",
		});
	},
});

const isDisabled = computed(
	() =>
		editor.tiptap?.isEmpty || ticket.replyViaAgent.loading || insertRes.loading
);

function removeAttachment(item) {
	editor.attachments = editor.attachments.filter((x) => x.name != item.name);
}

function newCommunication() {
	ticket.replyViaAgent.loading = true;
	ticket.replyViaAgent.submit({
		attachments: editor.attachments.map((x) => x.name),
		cc: editor.cc.join(","),
		bcc: editor.bcc.join(","),
		message: editor.content,
	});
}

function newComment() {
	insertRes.loading = true;
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
