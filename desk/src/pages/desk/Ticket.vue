<template>
	<div>
		<div v-if="ticket">
			<div class="flow-root pt-4 pb-6 pr-[26.14px] pl-[18px] h-[64px]">
			</div>
			<div
				v-if="ticket" 
				class="flex border-t w-full"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 4rem)' : null }"
			>
				<div class="border-r w-[252px] shrink-0">

				</div>
				<div class="grow">
					<div class="border-b py-[14px] px-[18.5px]">
						<div class="flow-root">
							<div class="float-left">
								<div class="flex items-center space-x-[13.5px]">
									<div>
										<CustomIcons name="comment" class="h-[25px] w-[25px] stroke-[#A6B1B9]" />
									</div>
									<div>
										<span class="font-semibold text-normal truncate">{{ ticket.subject }}</span>
									</div>
								</div>
							</div>
							<div class="float-right">
								<div class="flex items-center space-x-[8px]">
									<Button icon="chevron-left" appearance="minimal"/>
									<Button icon="chevron-right" appearance="minimal"/>
									<Button icon="more-horizontal" appearance="minimal"/>
								</div>
							</div>
						</div>
					</div>
				</div>
				<div class="border-l bg-gray-50 w-[252px] shrink-0">

				</div>
			</div>
		</div>
	</div>
</template>
<script>
import { Badge, Card, Dropdown, Avatar, FileUploader, FeatherIcon } from 'frappe-ui'
import ConversationAndActivities from '@/components/desk/ticket/ConversationAndActivities.vue';
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
		ConversationAndActivities,
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
		const show = ref('Conversations') // Conversations, Activities, All
		const attachments = ref([])
		
		return { 
			editor,
			viewportWidth,
			user,
			tickets,
			ticketController,
			show,
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