<template>
	<div>
		<div v-if="ticket" class="flex flex-col h-screen grow-0">
			<div class="h-[72px] px-[20px] flex">
				<router-link
					:to="{ path: '/frappedesk/tickets' }"
					class="h-[20px] my-[26px] text-[12px] text-gray-600 stroke-gray-600 flex flex-row items-center space-x-1 hover:text-gray-700 hover:stroke-gray-700 select-none"
					role="button"
				>
					<FeatherIcon name="arrow-left" class="w-[13px] h-[13px]" />
					<div>Back to Tickets</div>
				</router-link>
			</div>
			<div
				v-if="ticket"
				class="flex border-t w-full"
				:style="{
					height: viewportWidth > 768 ? 'calc(100vh - 72px)' : null,
				}"
			>
				<div class="border-r w-[252px] shrink-0">
					<ActionPanel :ticketId="ticket.name" />
				</div>
				<div
					class="grow flex flex-col h-full"
					:style="{ width: 'calc(100vh - 252px - 240px - 252px)' }"
				>
					<div class="border-b py-[14px] px-[18px]">
						<div class="flex flex-row justify-between">
							<div class="grow">
								<div
									class="grow flex flex-row items-center space-x-[13.5px]"
								>
									<div>
										<CustomIcons
											v-if="ticket.via_customer_portal"
											name="comment"
											class="h-[25px] w-[25px] stroke-[#A6B1B9]"
										/>
										<FeatherIcon
											v-else
											name="mail"
											class="h-[25px] w-[25px] p-[1.5px] stroke-[#A6B1B9]"
										/>
									</div>
									<a
										:title="ticket.subject"
										class="sm:max-w-[200px] lg:max-w-[550px] truncate cursor-pointer font-semibold"
									>
										{{ ticket.subject }}
									</a>
								</div>
							</div>
						</div>
					</div>
					<div class="grow overflow-y-scroll px-[17px]">
						<CustomerSatisfactionFeedback
							:fromDesk="true"
							v-if="
								ticket.feedback_submitted &&
								['Closed', 'Resolved'].includes(ticket.status)
							"
							class="mt-[10px]"
							:editable="false"
							:ticket="ticket"
						/>
						<Conversations
							:ticketId="ticket.name"
							:scrollToBottom="scrollConversationsToBottom"
							:autoScroll="
								['Open', 'Replied'].includes(ticket.status)
							"
						/>
					</div>
					<div
						class="shrink-0 flex flex-col mb-[15px] px-[18px] space-y-[11px] pt-2"
					>
						<TextEditor
							v-if="editing"
							ref="replyEditor"
							:content="content"
							editor-class="text-[13px] min-h-[180px] max-h-[300px] max-w-full overflow-y-scroll"
							v-on:keydown="handleShortcuts($event)"
							:mentions="mentions"
							@change="
								(val) => {
									content = val
								}
							"
							@click="$refs.replyEditor.editor.commands.focus()"
							:placeholder="
								editingType == 'reply'
									? 'Type a response'
									: 'Type a comment'
							"
							class="border border-gray-300 rounded-[8px] p-[12px]"
						>
							<template #top>
								<div
									class="flex flex-row items-center text-[12px] font-normal pb-[8px]"
								>
									<div v-if="editingType == 'reply'">
										<div
											v-if="ticket.raised_by"
											class="flex flex-row space-x-2 items-center"
										>
											<span class="text-gray-700"
												>to</span
											>
											<div
												class="bg-gray-50 rounded-[6px] px-[10px] py-[4px]"
											>
												{{ ticket.raised_by }}
											</div>
										</div>
									</div>
									<div
										v-else
										class="flex flex-row items-center space-x-2"
									>
										<span class="text-gray-700">as</span>
										<span
											class="text-[11px] text-gray-900 bg-[#FDF9F2] shadow font-normal border border-gray-400 rounded-[6px] px-[10px] py-[4px]"
											>Comment</span
										>
									</div>
									<div class="grow flex flex-row-reverse">
										<a
											role="button"
											@click="cancelEditing"
											title="Hide Editor"
										>
											<FeatherIcon
												name="chevron-down"
												class="h-4 w-4"
											/>
										</a>
									</div>
								</div>
							</template>
							<template #bottom>
								<div>
									<div
										v-if="attachments.length"
										class="max-h-[100px] overflow-y-scroll rounded flex flex-col"
									>
										<ul class="flex flex-wrap gap-2 py-2">
											<li
												class="flex items-center p-1 space-x-2 bg-gray-100 border-gray-400 border shadow rounded"
												v-for="file in attachments"
												:key="file"
												:title="file.name"
											>
												<div
													class="flex flex-row items-center space-x-1"
												>
													<FeatherIcon
														name="file-text"
														class="h-[15px] stroke-gray-600"
													/>
													<span
														class="text-[12px] text-gray-700 font-normal ml-2 max-w-[100px] truncate"
													>
														{{ file.file_name }}
													</span>
												</div>
												<button
													class="grid w-4 h-4 text-gray-700 rounded hover:bg-gray-300 place-items-center"
													@click="
														() => {
															attachments =
																attachments.filter(
																	(x) =>
																		x.name !=
																		file.name
																)
														}
													"
												>
													<FeatherIcon
														class="w-3"
														name="x"
													/>
												</button>
											</li>
										</ul>
									</div>
									<div v-if="showTextFormattingMenu">
										<TextEditorFixedMenu
											class="my-1 overflow-x-auto rounded shadow-sm border"
											:buttons="textEditorMenuButtons"
										/>
									</div>
									<div
										class="pt-2 select-none flex flex-row items-center space-x-2"
										v-if="$refs.replyEditor"
									>
										<Button
											:loading="
												editingType == 'reply'
													? $resources
															.submitConversation
															.loading
													: $resources.submitComment
															.loading
											"
											@click="submit()"
											appearance="primary"
											:disabled="
												(!user.agent &&
													!user.isAdmin) ||
												sendingDissabled
											"
										>
											{{
												editingType == "reply"
													? "Send"
													: "Create"
											}}
										</Button>
										<div
											class="flex flex-row items-center space-x-2"
										>
											<CustomIcons
												:class="
													showTextFormattingMenu
														? 'bg-gray-200'
														: ''
												"
												name="text-formatting"
												class="h-7 w-7 rounded p-1"
												role="button"
												@click="
													() => {
														showTextFormattingMenu =
															!showTextFormattingMenu
													}
												"
											/>
											<FileUploader
												@success="
													(file) =>
														attachments.push(file)
												"
											>
												<template
													v-slot="{
														progress,
														uploading,
														openFileSelector,
													}"
												>
													<FeatherIcon
														name="paperclip"
														class="h-[17px]"
														@click="
															openFileSelector
														"
														role="button"
														:disabled="uploading"
													/>
												</template>
											</FileUploader>
											<CustomIcons
												name="add-response"
												class="h-7 w-7 rounded p-1"
												role="button"
												@click="
													() => {
														showCannedResponsesDialog = true
													}
												"
											/>
											<CannedResponsesDialog
												:show="
													showCannedResponsesDialog
												"
												@messageVal="getMessage($event)"
												@close="
													() => {
														showCannedResponsesDialog = false
													}
												"
											/>
										</div>
										<div class="grow flex flex-row-reverse">
											<FeatherIcon
												name="trash-2"
												role="button"
												class="h-4 w-4"
												@click="
													() => {
														content = ''
														attachments = []
														editing = false
													}
												"
											/>
										</div>
									</div>
								</div>
							</template>
						</TextEditor>
						<div>
							<div
								v-if="!editing"
								class="flex flex-row space-x-[14px]"
							>
								<Button
									appearance="primary"
									@click="startEditing('reply')"
								>
									Reply
								</Button>
								<Button
									@click="startEditing('comment')"
									appearance="secondary"
									:disabled="!user.agent && !user.isAdmin"
								>
									Add Comment
								</Button>
							</div>
						</div>
					</div>
				</div>
				<div class="border-l bg-gray-50 w-[252px] shrink-0">
					<InfoPanel :ticketId="ticket.name" />
				</div>
			</div>
		</div>
	</div>
</template>
<script>
import {
	Badge,
	Card,
	Dropdown,
	Avatar,
	FileUploader,
	FeatherIcon,
	TextEditor,
} from "frappe-ui"
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor"
import Conversations from "@/components/desk/ticket/Conversations.vue"
import InfoPanel from "@/components/desk/ticket/InfoPanel.vue"
import ActionPanel from "@/components/desk/ticket/ActionPanel.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import CustomerSatisfactionFeedback from "@/components/portal/ticket/CustomerSatisfactionFeedback.vue"
import CannedResponsesDialog from "@/components/desk/global/CannedResponsesDialog.vue"
import { inject, ref } from "vue"

export default {
	name: "Ticket",
	props: ["ticketId"],
	components: {
		Badge,
		Card,
		Dropdown,
		Avatar,
		FileUploader,
		FeatherIcon,
		TextEditor,
		Conversations,
		InfoPanel,
		ActionPanel,
		CustomIcons,
		CustomerSatisfactionFeedback,
		CannedResponsesDialog,
		TextEditorFixedMenu,
	},
	data() {
		return {
			editing: false,
			scrollConversationsToBottom: false,
			content: "",
		}
	},
	setup() {
		const showTextFormattingMenu = ref(true)
		const viewportWidth = inject("viewportWidth")
		const user = inject("user")
		const agents = inject("agents")
		const attachments = ref([])

		const editingType = ref("")

		const tempTextEditorData = ref({})

		const showCannedResponsesDialog = ref(false)
		const tempMessage = ref("")

		return {
			showTextFormattingMenu,
			viewportWidth,
			user,
			agents,
			attachments,
			tempTextEditorData,
			editingType,
			showCannedResponsesDialog,
			tempMessage,
		}
	},
	resources: {
		submitConversation() {
			return {
				method: "frappedesk.api.ticket.submit_conversation_via_agent",
				onSuccess: (res) => {
					if (res.status == "error") {
						const error = {
							"No default outgoing email available": {
								title: "Email not sent",
								text: "No default outgoing email available",
							},
						}[res.error_code]

						this.$toast({
							fixed: true,
							title: error.title,
							text: error.text,
							customIcon: "circle-fail",
							appearance: "danger",
							fixed: true,
							action: {
								title: "Setup Now",
								onClick: () => {
									this.$router.push({ name: "Emails" })
								},
							},
						})
					}
					this.tempTextEditorData = {}
					this.editing = false
				},
				onError: () => {
					this.content = this.tempTextEditorData.content
					this.attachments = this.tempTextEditorData.attachments
				},
			}
		},
		submitComment() {
			return {
				method: "frappe.client.insert",
				onSuccess: () => {
					this.tempTextEditorData = {}
					this.editing = false
				},
				onError: () => {
					this.content = this.tempTextEditorData.content
					this.attachments = this.tempTextEditorData.attachments
				},
			}
		},
		markTicketAsSeen() {
			return {
				method: "frappedesk.api.ticket.mark_ticket_as_seen",
			}
		},
		ticket() {
			return {
				type: "document",
				doctype: "Ticket",
				name: this.ticketId,
			}
		},
	},
	mounted() {
		this.$resources.markTicketAsSeen.submit({
			ticket_id: this.ticketId,
		})
	},
	computed: {
		textEditorMenuButtons() {
			return [
				"Paragraph",
				[
					"Heading 2",
					"Heading 3",
					"Heading 4",
					"Heading 5",
					"Heading 6",
				],
				"Separator",
				"Bold",
				"Italic",
				"Separator",
				"Bullet List",
				"Numbered List",
				"Separator",
				"Align Left",
				"Align Center",
				"Align Right",
				"Separator",
				"Image",
				"Video",
				"Link",
				"Blockquote",
				"Code",
				"Horizontal Rule",
				[
					"InsertTable",
					"AddColumnBefore",
					"AddColumnAfter",
					"DeleteColumn",
					"AddRowBefore",
					"AddRowAfter",
					"DeleteRow",
					"MergeCells",
					"SplitCell",
					"ToggleHeaderColumn",
					"ToggleHeaderRow",
					"ToggleHeaderCell",
					"DeleteTable",
				],
				"Separator",
				"Undo",
				"Redo",
			]
		},
		ticket() {
			return this.$resources.ticket.doc || null
		},
		sendingDissabled() {
			let content = this.content.trim()
			content = content.replaceAll("<p></p>", "")
			content = content.replaceAll(" ", "")
			return (
				(content == "" ||
					content == "<p><br></p>" ||
					content == "<p></p>") &&
				this.attachments.length == 0
			)
		},
		mentions() {
			const users = this.editingType === "comment" ? this.agents : []
			return users.map((user) => ({
				label: user.agent_name,
				value: user.name,
			}))
		},
	},
	methods: {
		startEditing(type = "reply") {
			this.editing = true
			this.editingType = type
			this.delayedConversationScroll()
			this.$nextTick(() => {
				this.$refs.replyEditor.editor.commands.focus()
			})
		},
		cancelEditing() {
			this.editing = false
		},
		delayedConversationScroll() {
			function delay(time) {
				return new Promise((resolve) => setTimeout(resolve, time))
			}

			delay(400).then(() => (this.scrollConversationsToBottom = true))
			delay(1000).then(() => (this.scrollConversationsToBottom = false))
		},
		handleShortcuts(e) {
			if ((e.metaKey || e.ctrlKey) && e.keyCode === 13) {
				if (!this.sendingDissabled) {
					this.submit()
				}
			} else if ((e.metaKey || e.ctrlKey) && e.keyCode === 75) {
				this.$refs.replyEditor.editor.commands.insertLink()
			} else if (e.keyCode === 27) {
				this.cancelEditing()
			}
		},
		submit() {
			switch (this.editingType) {
				case "reply":
					this.submitConversation()
					break
				case "comment":
					this.submitComment()
					break
			}
		},
		submitConversation() {
			this.tempTextEditorData.content = this.content
			this.tempTextEditorData.attachments = this.attachments

			this.$resources.submitConversation.submit({
				ticket_id: this.ticketId,
				message: this.content,
				attachments: this.attachments.map((x) => x.name),
			})

			this.content = ""
			this.attachments = []
		},
		submitComment() {
			this.tempTextEditorData.attachments = this.attachments
			this.tempTextEditorData.content = this.content

			this.$resources.submitComment.submit({
				doc: {
					doctype: "Frappe Desk Comment",
					reference_ticket: this.ticketId,
					content: this.content,
					commented_by: this.user.user,
				},
			})

			this.content = ""
			this.attachments = []
		},
		getNextTicket() {},
		getPreviousTicket() {},

		getMessage(message) {
			this.tempMessage = message
			this.content = this.tempMessage
		},
	},
}
</script>
