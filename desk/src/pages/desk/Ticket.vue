<template>
	<div>
		<div v-if="ticket" class="flex flex-col h-screen">
			<div class="flow-root pt-4 pb-6 pr-[26.14px] pl-[18px] h-[64px]">
			</div>
			<div
				v-if="ticket" 
				class="flex border-t w-full"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 4rem)' : null }"
			>
				<div class="border-r w-[252px] shrink-0">

				</div>
				<div class="grow flex flex-col h-full">
					<div class="border-b py-[14px] px-[18.5px]">
						<div class="flex flex-row justify-between">
							<div>
								<div class="flex items-center space-x-[13.5px]">
									<div>
										<CustomIcons name="comment" class="h-[25px] w-[25px] stroke-[#A6B1B9]" />
									</div>
									<div>
										<span class="font-semibold text-normal">{{ ticket.subject }}</span>
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
						['bold', 'italic', 'underline', 'strike'],        // toggled buttons
						['blockquote', 'code-block'],

						[{ 'header': 1 }, { 'header': 2 }],               // custom button values
						[{ 'list': 'ordered'}, { 'list': 'bullet' }],

						[{ 'header': [1, 2, 3, 4, 5, 6, false] }],

						[{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
						
						['image'],
						
						[{ 'align': [] }],

						['clean']                                         // remove formatting button
					]
				},
				placeholder: 'Compose your reply...',
				theme: 'snow',
				bounds: 7,
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
		
		return { 
			editor,
			viewportWidth,
			user,
			tickets,
			ticketController,
			attachments
		}
	},
	resources: {
		submitConversation() {
			return {
				method: 'frappedesk.api.ticket.submit_conversation_via_agent',
				onSuccess: () => {
					var element = document.getElementsByClassName("ql-editor");
					element[0].innerHTML = "";
					this.attachments = []
				}
			}
		}
	},
	computed: {
		ticket() {
			if (this.ticketController.markAsSeen) {
				this.ticketController.markAsSeen(this.ticketId)
			}
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
			this.$resources.submitConversation.submit({
				ticket_id: this.ticketId,
				message: this.content,
				attachments: this.attachments.map(x => x.name)
			})
		},
		getNextTicket() {

		},
		getPreviousTicket() {

		}
	},
}
</script>