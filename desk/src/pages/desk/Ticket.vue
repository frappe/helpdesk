<template>
	<div class="overflow-hidden">
		<div v-if="ticket" class="flex h-screen grow-0 flex-col">
			<div class="flex h-[60px] px-[20px]">
				<div class="flex flex-row items-center space-x-2">
					<router-link
						:to="{ path: '/frappedesk/tickets' }"
						class="flex select-none flex-row items-center space-x-[12px] stroke-gray-600 text-[18px] font-semibold text-gray-900 hover:stroke-gray-700"
						role="button"
					>
						<FeatherIcon name="arrow-left" class="h-[12px] w-[12px]" />
						<div>Ticket #{{ ticket.name }}</div>
					</router-link>
					<TicketStatus :value="ticket.status" />
					<FeatherIcon
						name="copy"
						class="h-[24px] w-[24px] rounded-md bg-gray-100 stroke-gray-700 p-1"
						role="button"
						@click="copyTicketName"
					/>
				</div>
			</div>
			<div
				v-if="ticket"
				class="flex w-full border-t"
				:style="{
					height: viewportWidth > 768 ? 'calc(100vh - 60px)' : null,
				}"
			>
				<div class="w-[252px] shrink-0 border-r">
					<ActionPanel :ticket-id="ticket.name" />
				</div>
				<div
					class="flex h-full grow flex-col"
					:style="{ width: 'calc(100vh - 252px - 240px - 252px)' }"
				>
					<div class="border-b py-[14px] px-[18px]">
						<div class="flex flex-row justify-between">
							<div class="grow">
								<div class="flex grow flex-row items-center space-x-[13.5px]">
									<div>
										<CustomIcons
											v-if="ticket.via_customer_portal"
											name="comment"
											class="h-[25px] w-[25px] stroke-[#A6B1B9]"
										/>
										<FeatherIcon
											v-else
											name="mail"
											class="h-[25px] w-[25px] stroke-[#A6B1B9] p-[1.5px]"
										/>
									</div>
									<div
										v-if="!editingSubject"
										class="flex grow items-center justify-between"
									>
										<a
											:title="ticket.subject"
											class="cursor-pointer truncate font-semibold sm:max-w-[200px] lg:max-w-[550px]"
										>
											{{ ticket.subject }}
										</a>
										<FeatherIcon
											class="h-4 w-4 cursor-pointer"
											name="edit"
											@click="editingSubject = true"
										/>
									</div>
									<div
										v-else
										class="flex grow items-center justify-between gap-2"
									>
										<Input
											id="subjectInput"
											class="w-full"
											:value="ticket.subject"
											type="text"
											@change="subject = $event"
										/>
										<div class="flex flex-row gap-2">
											<Button
												appearance="primary"
												@click="
													() => {
														$resources.ticket.setValue
															.submit({
																subject: subject,
															})
															.then((editingSubject = false));
													}
												"
												>Save</Button
											>
											<Button appearance="secondary" @click="$router.go()"
												>Discard</Button
											>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
					<div class="grow overflow-y-scroll px-[17px]">
						<CustomerSatisfactionFeedback
							v-if="
								ticket.feedback_submitted &&
								['Closed', 'Resolved'].includes(ticket.status)
							"
							:from-desk="true"
							class="mt-[10px]"
							:editable="false"
							:ticket="ticket"
						/>
						<Conversations
							:ticket-id="ticket.name"
							:scroll-to-bottom="scrollConversationsToBottom"
							:auto-scroll="['Open', 'Replied'].includes(ticket.status)"
						/>
					</div>
					<div
						class="mb-[15px] flex shrink-0 flex-col space-y-[11px] px-[18px] pt-2"
					>
						<TextEditor
							v-if="editing"
							ref="replyEditor"
							:content="content"
							editor-class="text-[13px] min-h-[180px] max-h-[300px] max-w-full overflow-y-scroll"
							:mentions="mentions"
							:placeholder="
								editingType == 'reply' ? 'Type a response' : 'Type a comment'
							"
							class="rounded-[8px] border border-gray-300 p-[12px]"
							@keydown="handleShortcuts($event)"
							@change="
								(val) => {
									content = val;
								}
							"
							@click="$refs.replyEditor.editor.commands.focus()"
						>
							<template #top>
								<div
									class="flex flex-row border-b-[1px] border-[#F4F5F6] pb-[8px] text-[12px] font-normal"
								>
									<div
										v-if="editingType == 'reply'"
										class="flex flex-col gap-2"
									>
										<div
											v-if="ticket.raised_by"
											class="flex flex-row items-center gap-2"
										>
											<div class="text-gray-700">To</div>
											<div class="rounded-md bg-gray-100 px-2 py-1">
												{{ ticket.raised_by }}
											</div>
										</div>
										<div
											v-show="showCc"
											class="flex flex-row flex-wrap items-center gap-2"
										>
											<div class="text-gray-700">Cc</div>
											<div
												v-for="email in ccList"
												class="flex items-center rounded-md bg-gray-100"
												:class="{
													'bg-red-100': !validateEmail(email),
												}"
											>
												<div class="px-2 py-1">
													{{ email }}
												</div>
												<FeatherIcon
													name="x"
													class="h-5 cursor-pointer py-1 pr-2"
													@click="() => removeFromEmailList(ccList, email)"
												/>
											</div>
											<Input
												class="bg-white focus:bg-white"
												@keydown.prevent.enter="
													(e) => pushToEmailList(ccList, e)
												"
												@keydown.prevent.space="
													(e) => pushToEmailList(ccList, e)
												"
												@keydown.prevent.,="(e) => pushToEmailList(ccList, e)"
												@paste.prevent="(e) => onEmailListPaste(ccList, e)"
											/>
										</div>
										<div
											v-show="showBcc"
											class="flex flex-row flex-wrap items-center gap-2"
										>
											<div class="text-gray-700">Bcc</div>
											<div
												v-for="email in bccList"
												class="flex items-center rounded-md bg-gray-100"
												:class="{
													'bg-red-100': !validateEmail(email),
												}"
											>
												<div class="px-2 py-1">
													{{ email }}
												</div>
												<FeatherIcon
													name="x"
													class="h-5 cursor-pointer py-1 pr-2"
													@click="() => removeFromEmailList(bccList, email)"
												/>
											</div>
											<Input
												class="bg-white focus:bg-white"
												@keydown.prevent.enter="
													(e) => pushToEmailList(bccList, e)
												"
												@keydown.prevent.space="
													(e) => pushToEmailList(bccList, e)
												"
												@keydown.prevent.,="(e) => pushToEmailList(bccList, e)"
												@paste.prevent="(e) => onEmailListPaste(bccList, e)"
											/>
										</div>
									</div>
									<div v-else class="flex flex-row items-center space-x-2">
										<span class="text-gray-700">as</span>
										<span
											class="rounded-[6px] border border-gray-400 bg-[#FDF9F2] px-[10px] py-[4px] text-[11px] font-normal text-gray-900 shadow"
											>Comment</span
										>
									</div>
									<div class="flex grow flex-row-reverse gap-1.5">
										<a role="button" title="Hide Editor" @click="cancelEditing">
											<CustomIcons
												name="arrow-down"
												class="h-[24px] w-[24px]"
											/>
										</a>
										<div v-if="editingType == 'reply'">
											<Button
												v-if="showCcBtn"
												class="h-[24px] w-[24px] bg-transparent text-[#4C5A67]"
												label="Cc"
												title="Cc"
												@click="
													() => {
														showCc = true;
														showCcBtn = false;
													}
												"
											>
											</Button>
											<Button
												v-if="showBccBtn"
												class="h-[24px] w-[24px] bg-transparent text-[#4C5A67]"
												appearenece="secondary"
												label="Bcc"
												title="Bcc"
												@click="
													() => {
														showBcc = true;
														showBccBtn = false;
													}
												"
											>
											</Button>
										</div>
									</div>
								</div>
							</template>
							<template #bottom>
								<div>
									<div
										v-if="attachments.length"
										class="flex max-h-[100px] flex-col overflow-y-scroll rounded"
									>
										<ul class="flex flex-wrap gap-2 py-2">
											<li
												v-for="file in attachments"
												:key="file"
												class="flex items-center space-x-2 rounded border border-gray-400 bg-gray-100 p-1 shadow"
												:title="file.name"
											>
												<div class="flex flex-row items-center space-x-1">
													<FeatherIcon
														name="file-text"
														class="h-[15px] stroke-gray-600"
													/>
													<span
														class="ml-2 max-w-[100px] truncate text-[12px] font-normal text-gray-700"
													>
														{{ file.file_name }}
													</span>
												</div>
												<button
													class="grid h-4 w-4 place-items-center rounded text-gray-700 hover:bg-gray-300"
													@click="
														() => {
															attachments = attachments.filter(
																(x) => x.name != file.name
															);
														}
													"
												>
													<FeatherIcon class="w-3" name="x" />
												</button>
											</li>
										</ul>
									</div>
									<div v-if="showTextFormattingMenu">
										<TextEditorFixedMenu
											class="my-1 overflow-x-auto rounded border shadow-sm"
											:buttons="textEditorMenuButtons"
										/>
									</div>
									<div
										v-if="$refs.replyEditor"
										class="flex select-none flex-row items-center gap-2 space-x-2 pt-2"
									>
										<div class="flex">
											<Dropdown
												v-if="editingType == 'reply'"
												placement="right"
												:button="{
													class: 'rounded-r-none',
													disabled:
														(!authStore.agent && !authStore.isAdmin) || sendingDissabled,
													appearance: 'primary',
													label: 'Menu',
													icon: 'chevron-up',
												}"
												:options="[
													{
														label: 'Send and set as Replied',
														handler: () => {
															submit();
															submitAndUpdateTicketStatus('Replied');
															$router.go();
														},
													},
													{
														label: 'Send and set as Resolved',
														handler: () => {
															submit();
															submitAndUpdateTicketStatus('Resolved');
															$router.go();
														},
													},
													{
														label: 'Send and set as Closed',
														handler: () => {
															submit();
															submitAndUpdateTicketStatus('Closed');
															$router.go();
														},
													},
												]"
											/>
											<Button
												class="[&:nth-child(2)]:rounded-l-none"
												:loading="
													editingType == 'reply'
														? $resources.ticket.replyViaAgent.loading
														: $resources.submitComment.loading
												"
												appearance="primary"
												:disabled="
													(!authStore.agent && !authStore.isAdmin) || sendingDissabled
												"
												@click="submit()"
											>
												{{ editingType == "reply" ? "Send" : "Create" }}
											</Button>
										</div>
										<div class="flex flex-row items-center space-x-2">
											<CustomIcons
												:class="showTextFormattingMenu ? 'bg-gray-200' : ''"
												name="text-formatting"
												class="h-7 w-7 rounded p-1"
												role="button"
												@click="
													() => {
														showTextFormattingMenu = !showTextFormattingMenu;
													}
												"
											/>
											<FileUploader @success="(file) => attachments.push(file)">
												<template
													#default="{ progress, uploading, openFileSelector }"
												>
													<FeatherIcon
														name="paperclip"
														class="h-[17px]"
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
												@click="
													() => {
														showCannedResponsesDialog = true;
													}
												"
											/>
											<CustomIcons
												name="article-reply"
												class="h-7 w-7 rounded p-1"
												role="button"
												@click="
													() => {
														showArticleResponseDialog = true;
													}
												"
											/>
											<CannedResponsesDialog
												:show="showCannedResponsesDialog"
												@messageVal="getMessage($event)"
												@close="
													() => {
														showCannedResponsesDialog = false;
													}
												"
											/>

											<ArticleResponseDialog
												:show="showArticleResponseDialog"
												@contentVal="getContent($event)"
												@close="
													() => {
														showArticleResponseDialog = false;
													}
												"
											/>
										</div>
										<div class="flex grow flex-row-reverse">
											<FeatherIcon
												name="trash-2"
												role="button"
												class="h-4 w-4"
												@click="
													() => {
														content = '';
														attachments = [];
														editing = false;
													}
												"
											/>
										</div>
									</div>
								</div>
							</template>
						</TextEditor>
						<div>
							<div v-if="!editing" class="flex flex-row space-x-[14px]">
								<Button appearance="primary" @click="startEditing('reply')">
									Reply
								</Button>
								<Button
									appearance="secondary"
									:disabled="!authStore.agent && !authStore.isAdmin"
									@click="startEditing('comment')"
								>
									Add Comment
								</Button>
							</div>
						</div>
					</div>
				</div>
				<div class="w-[252px] shrink-0 border-l bg-gray-50">
					<InfoPanel :ticket-id="ticket.name" />
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { inject, ref } from "vue";
import {
	ErrorMessage,
	Badge,
	Card,
	Dropdown,
	Avatar,
	FileUploader,
	FeatherIcon,
	TextEditor,
} from "frappe-ui";
import * as zod from "zod";
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor";
import Conversations from "@/components/desk/ticket/Conversations.vue";
import InfoPanel from "@/components/desk/ticket/InfoPanel.vue";
import ActionPanel from "@/components/desk/ticket/ActionPanel.vue";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";
import CustomerSatisfactionFeedback from "@/components/portal/ticket/CustomerSatisfactionFeedback.vue";
import CannedResponsesDialog from "@/components/desk/global/CannedResponsesDialog.vue";
import ArticleResponseDialog from "@/components/desk/global/ArticleResponseDialog.vue";
import TicketStatus from "@/components/global/ticket_list_item/TicketStatus.vue";
import { useAuthStore } from "@/stores/auth";
import { TextEditorMenuButtons } from "./consts";

export default {
	name: "Ticket",
	components: {
		ActionPanel,
		ArticleResponseDialog,
		Avatar,
		Badge,
		CannedResponsesDialog,
		Card,
		Conversations,
		CustomIcons,
		CustomerSatisfactionFeedback,
		Dropdown,
		ErrorMessage,
		FeatherIcon,
		FileUploader,
		InfoPanel,
		TextEditor,
		TextEditorFixedMenu,
		TicketStatus,
	},
	props: {
		ticketId: String,
	},
	setup() {
		const showTextFormattingMenu = ref(true);
		const viewportWidth = inject("viewportWidth");
		const authStore = useAuthStore();
		const agents = inject("agents");
		const attachments = ref([]);
		const editingType = ref("");
		const replied = ref("Replied");
		const tempTextEditorData = ref({});
		const showCannedResponsesDialog = ref(false);
		const tempMessage = ref("");
		const showArticleResponseDialog = ref(false);
		const tempContent = ref("");
		const editingSubject = ref("");
		const showCc = ref(false);
		const showBcc = ref(false);
		const showCcBtn = ref(true);
		const showBccBtn = ref(true);

		const ccList = ref([]);
		const bccList = ref([]);

		return {
			ccList,
			bccList,
			showTextFormattingMenu,
			viewportWidth,
			authStore,
			agents,
			attachments,
			tempTextEditorData,
			editingType,
			showCannedResponsesDialog,
			tempMessage,
			showArticleResponseDialog,
			tempContent,
			editingSubject,
			replied,
			showCc,
			showBcc,
			showCcBtn,
			showBccBtn,
			replied,
		};
	},
	data() {
		return {
			editing: false,
			scrollConversationsToBottom: false,
			content: "",
			textEditorMenuButtons: TextEditorMenuButtons,
		};
	},
	resources: {
		ticket() {
			return {
				type: "document",
				doctype: "Ticket",
				name: this.ticketId,
				onSuccess: () => {
					this.$resources.ticket.lastCommunication.fetch();
				},
				whitelistedMethods: {
					lastCommunication: {
						method: "last_communication",
						onSuccess: (data) => {
							this.ccList = this.ccList.length
								? this.ccList
								: data.cc?.split(",") || [];
							this.bccList = this.bccList.length
								? this.bccList
								: data.bcc?.split(",") || [];
						},
					},
					markSeen: "mark_seen",
					replyViaAgent: {
						method: "reply_via_agent",
						onSuccess: () => {
							this.tempTextEditorData = {};
							this.editing = false;
						},
						onError: ({ error }) => {
							this.content = this.tempTextEditorData.content;
							this.attachments = this.tempTextEditorData.attachments;
							const text = error?.messages
								?.filter((v, i, s) => s.indexOf(v) == i)
								?.join("\n");

							if (!text) return;

							this.$toast({
								text,
								icon: "x",
								iconClasses: "text-red-500",
							});
						},
					},
				},
			};
		},
		submitComment() {
			return {
				url: "frappe.client.insert",
				onSuccess: () => {
					this.tempTextEditorData = {};
					this.editing = false;
				},
				onError: () => {
					this.content = this.tempTextEditorData.content;
					this.attachments = this.tempTextEditorData.attachments;
				},
			};
		},
	},
	computed: {
		ticket() {
			return this.$resources.ticket.doc || null;
		},
		sendingDissabled() {
			let content = this.content.trim();
			content = content.replaceAll("<p></p>", "");
			content = content.replaceAll(" ", "");
			return (
				(content == "" || content == "<p><br></p>" || content == "<p></p>") &&
				this.attachments.length == 0
			);
		},
		mentions() {
			const users = this.editingType === "comment" ? this.agents : [];
			return users.map((user) => ({
				label: user.agent_name,
				value: user.name,
			}));
		},
	},
	mounted() {
		this.$resources.ticket.markSeen.submit();
	},
	methods: {
		async copyTicketName() {
			this.$clipboardCopy(this.ticket.name);
		},
		startEditing(type = "reply") {
			this.editing = true;
			this.editingType = type;
			this.delayedConversationScroll();
			this.$nextTick(() => {
				this.$refs.replyEditor.editor.commands.focus();
			});
		},
		cancelEditing() {
			this.editing = false;
		},
		delayedConversationScroll() {
			function delay(time) {
				return new Promise((resolve) => setTimeout(resolve, time));
			}
			delay(400).then(() => (this.scrollConversationsToBottom = true));
			delay(1000).then(() => (this.scrollConversationsToBottom = false));
		},
		handleShortcuts(e) {
			if ((e.metaKey || e.ctrlKey) && e.keyCode === 13) {
				if (!this.sendingDissabled) {
					this.submit();
				}
			} else if ((e.metaKey || e.ctrlKey) && e.keyCode === 75) {
				this.$refs.replyEditor.editor.commands.insertLink();
			} else if (e.keyCode === 27) {
				this.cancelEditing();
			}
		},
		submit() {
			switch (this.editingType) {
				case "reply":
					this.submitConversation();
					break;
				case "comment":
					this.submitComment();
					break;
			}
		},
		submitConversation() {
			this.tempTextEditorData.content = this.content;
			this.tempTextEditorData.attachments = this.attachments;
			const message = `<div class='content-block'><div>${this.content}</div></div>`;

			this.$resources.ticket.replyViaAgent.submit({
				attachments: this.attachments.map((x) => x.name),
				bcc: this.bccList.join(","),
				cc: this.ccList.join(","),
				message,
			});

			this.content = "";
			this.attachments = [];
		},
		submitAndUpdateTicketStatus(status) {
			this.$resources.ticket.update.submit({
				status: status,
			});
			this.submitConversation();
		},
		submitResolvedTicket() {
			this.tempTextEditorData.content = this.content;
			this.tempTextEditorData.attachments = this.attachments;
			const content = `<div class='content-block'><div>${this.content}</div></div>`;

			this.$resources.ticket.update.submit({
				status: "Resolved",
			});

			this.$resources.ticket.replyViaAgent.submit({
				message: content,
				attachments: this.attachments.map((x) => x.name),
			});

			this.content = "";
			this.attachments = [];
		},
		submitComment() {
			this.tempTextEditorData.attachments = this.attachments;
			this.tempTextEditorData.content = this.content;
			const content = `<div class='content-block'><div>${this.content}</div></div>`;
			this.$resources.submitComment.submit({
				doc: {
					doctype: "Frappe Desk Comment",
					reference_ticket: this.ticketId,
					content: content,
					commented_by: this.authStore.userId,
				},
			});
			this.content = "";
			this.attachments = [];
		},
		getMessage(message) {
			this.tempMessage = message;
			this.content = this.tempMessage;
		},
		getContent(content) {
			this.tempContent = content;
			this.content = this.tempContent;
		},
		validateEmail(email) {
			return zod.string().email().safeParse(email).success;
		},
		pushToEmailList(list, e) {
			if (typeof e === "string") {
				if (!this.validateEmail(e)) return;
				list.push(e);
				return;
			}

			if (list.indexOf(e.target.value) > 0) return;

			if (!this.validateEmail(e.target.value)) {
				this.$toast({
					title: "Invalid email",
					icon: "x",
					iconClasses: "text-red-500",
				});

				return;
			}

			list.push(e.currentTarget.value);
			e.currentTarget.value = "";
		},
		removeFromEmailList(list, email) {
			list.splice(list.indexOf(email), 1);
		},
		onEmailListPaste(list, e) {
			const d = e.clipboardData.getData("text/plain");
			const delimiter = d.includes(",") ? "," : " ";

			d.split(delimiter)
				.map((email) => email.trim())
				.forEach((email) => this.pushToEmailList(list, email));
		},
	},
};
</script>
