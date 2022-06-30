<template>
	<div>
		<div v-if="ticket" class="flex flex-col h-screen grow-0">
			<div class="h-[72px] px-[20px]">
				<router-link 
					:to="(prevRoute && prevRoute.path === '/frappedesk/tickets') ? prevRoute : {path: '/frappedesk/tickets', query: {menu_filter: ticketSideBarFilter}}"
					class="h-[20px] my-[26px] text-[12px] text-gray-600 stroke-gray-600 flex flex-row items-center space-x-1 hover:text-gray-700 hover:stroke-gray-700 select-none"
					role="button"
				>
					<FeatherIcon name="arrow-left" class="w-[13px] h-[13px]" />
					<div> Back to {{ sideBarFilterMap[ticketSideBarFilter] }} </div>
				</router-link>
			</div>
			<div
				v-if="ticket" 
				class="flex border-t w-full"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 72px)' : null }"
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
										<CustomIcons v-if="ticket.via_customer_portal" name="comment" class="h-[25px] w-[25px] stroke-[#A6B1B9]" />
										<FeatherIcon v-else name="mail" class="h-[25px] w-[25px] p-[1.5px] stroke-[#A6B1B9]" />
									</div>
									<a :title="ticket.subject" class="sm:max-w-[200px] lg:max-w-[550px] truncate cursor-pointer font-semibold">
										{{ ticket.subject }}
									</a>
								</div>
							</div>
						</div>
					</div>
					<div class="grow overflow-scroll px-[18px]">
						<CustomerSatisfactionFeedback :fromDesk="true" v-if="ticket.feedback_submitted && ['Closed', 'Resolved'].includes(ticket.status)" class="mt-[10px]" :editable="false" :ticket="ticket"/>
						<Conversations :ticketId="ticket.name" :scrollToBottom="scrollConversationsToBottom" :autoScroll="['Open', 'Replied'].includes(ticket.status)" />
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
								<div v-if="editingType === 'reply'" class="border-b border-l border-r border-gray-400 p-2 select-none">
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
										:loading="editingType == 'reply' ? $resources.submitConversation.loading : $resources.submitComment.loading" 
										@click="submit()" 
										appearance="primary" 
										:disabled="(!user.agent && !user.isAdmin) || sendingDeissabled"
									>
										Send
									</Button>
									<Button appearance="secondary" @click="cancelEditing()">
										Cancel
									</Button>
								</div>
							</div>
							<div v-else class="flex flex-row space-x-[14px]">
								<Button appearance="primary" @click="startEditing('reply')">
									Reply 
								</Button>
								<Button 
									@click="startEditing('comment')"
									appearance="secondary" 
									:disabled="(!user.agent && !user.isAdmin)"
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
import { Badge, Card, Dropdown, Avatar, FileUploader, FeatherIcon } from 'frappe-ui'
import Conversations from '@/components/desk/ticket/Conversations.vue';
import InfoPanel from '@/components/desk/ticket/InfoPanel.vue';
import ActionPanel from '@/components/desk/ticket/ActionPanel.vue';
import CustomIcons from '@/components/desk/global/CustomIcons.vue';
import { QuillEditor } from '@vueup/vue-quill'
import CustomerSatisfactionFeedback from '@/components/portal/ticket/CustomerSatisfactionFeedback.vue';
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
		QuillEditor,
		CustomerSatisfactionFeedback
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
									this.submit();
								}
							}
						}
					}
				},
				placeholder: 'Compose your reply...',
				theme: 'snow',
				bounds: document.body,
			},
			prevRoute: null

		}
	},
	beforeRouteEnter(to, from, next) {
		next(vm => {
			vm.prevRoute = from
		})
	},
	setup() {
		const editor = ref(null);
		const viewportWidth = inject('viewportWidth')
		const user = inject('user')
		const attachments = ref([])

		const editingType = ref('')

		const tempTextEditorData = ref({})
		
		const sideBarFilterMap = inject('sideBarFilterMap')
		const ticketSideBarFilter = inject('ticketSideBarFilter')
		
		return { 
			editor,
			viewportWidth,
			user,
			attachments,
			tempTextEditorData,
			editingType,
			sideBarFilterMap,
			ticketSideBarFilter
		}
	},
	resources: {
		submitConversation() {
			return {
				method: 'frappedesk.api.ticket.submit_conversation_via_agent',
				onSuccess: () => {
					this.tempTextEditorData = {}
					this.editing = false
				},
				onError: () => {
					var element = document.getElementsByClassName("ql-editor");
					element[0].innerHTML = this.tempTextEditorData.innerHTML;
					this.attachments = this.tempTextEditorData.attachments
				}
			}
		},
		submitComment() {
			return {
				method: 'frappe.client.insert',
				onSuccess: () => {
					this.tempTextEditorData = {}
					this.editing = false
				},
				onError: () => {
					var element = document.getElementsByClassName("ql-editor");
					element[0].innerHTML = this.tempTextEditorData.innerHTML;
					this.attachments = this.tempTextEditorData.attachments
				}
			}
		},
		markTicketAsSeen() {
			return {
				method: 'frappedesk.api.ticket.mark_ticket_as_seen'
			}
		},
		ticket() {
			return {
				type: 'document',
				doctype: 'Ticket',
				name: this.ticketId
			}
		}
	},
	mounted() {
		this.$resources.markTicketAsSeen.submit({
			ticket_id: this.ticketId
		})
	},
	computed: {
		ticket() {
			return this.$resources.ticket.doc || null
		},
		sendingDeissabled() {
			let content = this.content.trim()
			return (content == "" || content == "<p><br></p>") && this.attachments.length == 0
		}
	},
	methods: {
		startEditing(type='reply') {
			this.editing = true
			this.editingType = type
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
		submit() {
			switch(this.editingType) {
				case 'reply':
					this.submitConversation()
					break
				case 'comment':
					this.submitComment()
					break
			}
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
		submitComment() {
			var element = document.getElementsByClassName("ql-editor");

			this.tempTextEditorData.attachments = this.attachments
			this.tempTextEditorData.innerHTML = element[0].innerHTML

			this.$resources.submitComment.submit({
				doc: {
					doctype: 'Comment',
					comment_type: 'Comment',
					reference_doctype: 'Ticket',
					reference_name: this.ticketId,
					content: this.content
				}
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