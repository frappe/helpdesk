<template>
	<div>
		<div v-if="ticket" class="flex flex-col h-screen grow-0">
			<div class="flow-root pt-4 pb-6 pr-[26.14px] pl-[18px] h-[64px]">
			</div>
			<div
				v-if="ticket" 
				class="flex border-t w-full"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 4rem)' : null }"
			>
				<div class="border-r w-[252px] shrink-0">
					<ActionPanel :ticketId="ticket.name" />
				</div>
				<div class="grow flex flex-col h-full overflow-x-scroll" :style="{ width: 'calc(100vh - 252px - 240px - 252px)' }">
					<div class="border-b py-[14px] px-[18px]">
						<div class="flex flex-row justify-between">
							<div class="grow">
								<div class="grow flex flex-row items-center space-x-[13.5px]">
									<div>
										<CustomIcons name="comment" class="h-[25px] w-[25px] stroke-[#A6B1B9]" />
									</div>
									<div class="group select-none">
										<div class="sm:max-w-[200px] lg:max-w-[550px] truncate cursor-pointer font-semibold">
											{{ ticket.subject }}
										</div>
										<div class="lg:max-w-[500px] sm:max-w-[200px] text-base hidden py-[8px] px-[12px] absolute z-50 bg-white border rounded shadow mt-[9px] group-hover:block">
											<p>{{ ticket.subject }}</p>
										</div>
									</div>
								</div>
							</div>
							<div class="flex flex-row items-center space-x-[8px]">
								<Button icon="chevron-left" appearance="minimal"/>
								<Button icon="chevron-right" appearance="minimal"/>
								<Button icon="more-horizontal" appearance="minimal"/>
							</div>
						</div>
					</div>
					<div class="grow overflow-scroll px-[18px]">
						<Conversations :ticketId="ticket.name" :scrollToBottom="scrollConversationsToBottom" />
					</div>
					<div class="shrink-0 flex flex-col pb-[19px] px-[18px] pt-[11px] space-y-[11px]">
						<div>
							<div v-if="editing">
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
							</div>
						</div>
						<div>
							<div v-if="editing">
								<div class="flex flex-row space-x-[14px]">
									<Button 
										:loading="this.$resources.submitConversation.loading" 
										@click="this.submitConversation" 
										appearance="primary" 
										:disabled="(!user.agent && !user.isAdmin) || sendButtonDissabled"
									>
										Send
									</Button>
									<Button appearance="secondary" @click="cancelEditing()">
										Cancel
									</Button>
								</div>
							</div>
							<div v-else>
								<Button appearance="primary" @click="startEditing()">
									Reply 
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
import { Badge, Card, Dropdown, Avatar, FileUploader, FeatherIcon } from 'frappe-ui'
import Conversations from '@/components/desk/ticket/Conversations.vue';
import InfoPanel from '@/components/desk/ticket/InfoPanel.vue';
import ActionPanel from '@/components/desk/ticket/ActionPanel.vue';
import CustomIcons from '@/components/desk/global/CustomIcons.vue';
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css';
import { inject, ref } from 'vue'

export default {
	name: 'Ticket',
	props: ['ticketId'],
	components: {
		Badge,
		Card,
		Dropdown,
		Avatar,
		FileUploader,
		FeatherIcon,
		Conversations,
		InfoPanel,
		ActionPanel,
		CustomIcons,
		QuillEditor
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
							// Ctrl+Enter to send reply
							ctrlEnter: {
								key: 13,
								shortKey: true,
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
		const editor = ref(null);
		const viewportWidth = inject('viewportWidth')
		const user = inject('user')
		const tickets = inject('tickets')
		const ticketController = inject('ticketController')
		const attachments = ref([])

		const tempTextEditorData = ref({})
		
		return { 
			editor,
			viewportWidth,
			user,
			tickets,
			ticketController,
			attachments,
			tempTextEditorData
		}
	},
	resources: {
		submitConversation() {
			return {
				method: 'frappedesk.api.ticket.submit_conversation_via_agent',
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
	mounted() {
		if (this.ticketController.markAsSeen) {
			this.ticketController.markAsSeen(this.ticketId)
		}
	},
	computed: {
		ticket() {
			return this.tickets[this.ticketId] || null
		},
		sendButtonDissabled() {
			let content = this.content.trim()
			return (content == "" || content == "<p><br></p>") && this.attachments.length == 0
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
		cancelEditing() {
			this.editing = false
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
		getNextTicket() {

		},
		getPreviousTicket() {

		}
	},
}
</script>
<style scoped>
*::-webkit-scrollbar {
	width: 0px;
	height: 0px;
}
</style>