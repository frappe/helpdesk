<template>
	<div v-if="ticket" class="max-w-4xl mx-auto">
		<div 
			:style="{ height: viewportWidth > 768 ? 'calc(100vh - 14rem)' : null }"
		>
			<div class="flex justify-between mb-4">
				<div class="flex items-center space-x-2 text-lg">
					<a href="/support/kb">Home</a>
					<FeatherIcon name="chevron-right" class="h-3 w-3"/>
					<router-link :to="{name: 'ProtalTickets'}">Tickets</router-link>
					<FeatherIcon name="chevron-right" class="h-3 w-3"/>
					<div class="text-gray-400">{{ ticket.name }}</div>
				</div>
				<div>
					<Button v-if="['Open', 'Replied'].includes(ticket.status)" @click="closeTicket()" class="bg-gray-100 text-red-500">Close</Button>
				</div>
			</div>
			<div class="flex items-center pb-2 justify-between">
				<div class="text-5xl font-bold">
					{{ ticket.subject }}
				</div>
			</div>
			<div class="grow flex flex-col h-full space-y-2">
				<div class="overflow-auto grow">
					<Conversations :ticketId="ticket.name" :scrollToBottom="scrollConversationsToBottom"/>
				</div>
				<div v-if="!editing && ['Open', 'Replied'].includes(ticket.status)" class="mt-5 ml-9">
					<Button @click="startEditing()" appearance="primary">Reply</Button>
				</div>
				<div
					v-if="editing"
					class="flex flex-col pr-3 pb-3" 
				>
					<div class="grow ml-3">
						<div v-if="!(['Closed', 'Resolved'].includes(ticket.status))">
							<quill-editor 
								:ref="editor"
								v-model:content="content" 
								contentType="html" 
								:options="editorOptions"
								style="min-height:150px; max-height:200px; overflow-y: auto;"
								@click="focusEditor()"
							/>
							<div class="border-b border-l border-r border-gray-400 p-2 select-none">
								<div class="w-full">
									<FileUploader @success="(file) => attachments.push(file)">
										<template
											v-slot="{ progress, uploading, openFileSelector }"
										>
											<div class="flex flex-row justify-between space-x-2 items-center">
												<div class="flex flex-row space-x-2">
													<div v-for="file in attachments" :key="file.name">
														<div class="flex space-x-2 items-center text-base bg-white border border-gray-400 rounded-md px-3 py-1">
															<div class="inline-block max-w-[100px] truncate">
																{{ file.file_name }}
															</div>
															<div>
																<FeatherIcon name="x" class="h-3 w-3 cursor-pointer hover:stroke-red-400 stroke-3" @click="() => {
																	attachments = attachments.filter(x => x.name != file.name)
																}"/>
															</div>
														</div>
													</div>
												</div>
												<div>
													<Button icon-left="plus" appearance="primary" class="inline-block" @click="openFileSelector" :loading="uploading">
														{{ uploading ? `Uploading ${progress}%` : 'Attachment' }}
													</Button>
												</div>
											</div>
										</template>
									</FileUploader>
								</div>
							</div>
							<div class="mt-2 space-x-2 flex">
								<Button 
									:disabled="sendButtonDissabled"
									:loading="this.$resources.submitConversation.loading" 
									@click="this.submitConversation" 
									appearance="primary" 
								>
									Send
								</Button>
								<Button @click="() => {editing = false}">Cancel</Button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { inject, ref } from "vue"
import Conversations from "@/components/portal/ticket/Conversations.vue"
import ActionPanel from "@/components/portal/ticket/ActionPanel.vue"
import '@vueup/vue-quill/dist/vue-quill.snow.css';
import { QuillEditor } from '@vueup/vue-quill'
import { FeatherIcon, FileUploader } from 'frappe-ui'

export default {
    name: "Tickets",
    props: ["ticketId"],
	components: {
		Conversations,
		ActionPanel,
		QuillEditor,
		FeatherIcon,
		FileUploader
	},
	data() {
		return {
			editing: false,
			scrollConversationsToBottom: false,
			content: "",
			editorOptions: {
				modules: {
					toolbar: [
						['bold', 'italic', 'underline', 'strike', 'link'],        // toggled buttons
						['blockquote', 'code-block'],

						[{ 'header': 1 }, { 'header': 2 }],               // custom button values
						[{ 'list': 'ordered'}, { 'list': 'bullet' }],

						[{ 'header': [1, 2, 3, 4, 5, 6, false] }],

						[{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
						
						['image'],
						
						[{ 'align': [] }],

						['clean']                                         // remove formatting button
					],
					keyboard: {
						bindings: {
							// Cmd+Enter to send reply
							cmdEnter: {
								key: 13,
								ctrlKey: true,
								handler: () => {
									this.submitConversation();
								}
							}
						}
					}
				},
				placeholder: 'Compose your reply...',
				theme: 'snow',
				bounds: document.body,
			}
		}
	},
    setup() {
		const editor = ref(null)
		const viewportWidth = inject("viewportWidth")
        const tickets = inject("tickets")
        const ticketController = inject("ticketController")
		const attachments = ref([])
		const tempTextEditorData = ref({})
        
		return { editor, viewportWidth, tickets, ticketController, attachments, tempTextEditorData }
    },
    computed: {
        ticket() {
			if (this.tickets) {
				return this.tickets[this.ticketId] || null
			} else {
				return null
			}
        },
		sendButtonDissabled() {
			let content = this.content.trim()
			return (content == "" || content == "<p><br></p>") && this.attachments.length == 0
		}
    },
	resources: {
		submitConversation() {
			return {
				method: 'frappedesk.api.ticket.submit_conversation_via_contact',
				onSuccess: () => {
					this.tempTextEditorData = {}
				},
				onError: () => {
					var element = document.getElementsByClassName("ql-editor");
					element[0].innerHTML = this.tempTextEditorData.innerHTML;
					this.attachments = this.tempTextEditorData.attachments
				}
			}
		}
	},
	methods: {
		startEditing() {
			this.editing = true
			this.delayedConversationScroll()
			this.$nextTick(() => {
				this.focusEditor()
			})
		},
		focusEditor() {
			var element = document.getElementsByClassName("ql-editor");
			element[0].focus() // TODO: focus the cursor to the end of the text
		},
		delayedConversationScroll() {
			function delay(time) {
				return new Promise(resolve => setTimeout(resolve, time));
			}

			delay(400).then(() => this.scrollConversationsToBottom = true)
			delay(1000).then(() => this.scrollConversationsToBottom = false)
		},
		submitConversation() {
			var element = document.getElementsByClassName("ql-editor");

			this.tempTextEditorData.attachments = this.attachments
			this.tempTextEditorData.innerHTML = element[0].innerHTML

			this.$resources.submitConversation.submit({
				ticket_id: this.ticketId,
				message: this.content,
				attachments: this.attachments.map(x => x.name)
			})

			element[0].innerHTML = "";
			this.attachments = []
		},
		closeTicket() {
			this.ticketController.set(this.ticketId, 'status', 'Closed')
		},
		reopenTicket() {
			this.ticketController.set(this.ticketId, 'status', 'Open')
		}
	}
}
</script>