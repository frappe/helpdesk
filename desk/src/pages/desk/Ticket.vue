<template>
	<div v-if="ticket">
		<TopControlPanel :ticket="ticket" @next="getNextTicket" @previous="getPreviousTicket"/>
		<div class="flex">
			<div 
				class="w-1/5 border-r"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.5rem)' : null }"
			>
				<InfoPanel :ticketId="ticket.name" />
			</div>
			<div
				class="w-3/5 pt-3 px-4"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 10.5rem)' : null }"
			>
				<div class="flex items-center pb-4">
					<span class="text-4xl truncate">
						{{ ticket.subject }}
					</span>
				</div>
				<div class="flex flex-col h-full space-y-2">
					<div class="overflow-auto grow">
						<Conversations :ticketId="ticket.name" :scrollToBottom="scrollConversationsToBottom"/>
					</div>
					<div class="flex flex-col pr-3 pb-10 pt-3">
						<div class="flex" v-if="editing">
							<div v-if="user.agent">
								<Avatar :imageURL="user.profile_image" size="md" />
							</div>
							<div class="grow ml-3">
								<div v-if="editing">
									<quill-editor 
										:ref="editor"
										v-model:content="content" 
										contentType="html" 
										:options="editorOptions"
										style="min-height:150px; max-height:200px; overflow-y: auto;"
									/>
									<div class="mt-2 space-x-2">
										<Button 
											:loading="this.$resources.submitConversation.loading" 
											@click="this.submitConversation" 
											appearance="primary" 
											:disabled="!user.agent && !user.isAdmin"
										>
											Send
										</Button>
										<Button 
											appearance="secondary" 
											@click="cancelEditing()"
										>
											Cancel
										</Button>
									</div>
								</div>
							</div>
						</div>
						<div class="flex space-x-2" v-else>
							<Button appearance="primary" @click="startEditing()">Reply</Button>
							<Button appearance="secondary">Comment</Button>
						</div>
					</div>
				</div>
			</div>
			<div 
				class="w-1/5 border-l"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.5rem)' : null }"
			>
				<ActionPanel :ticketId="ticket.name" />
			</div>
		</div>
	</div>
</template>
<script>
import { Badge, Card, Dropdown, Avatar } from 'frappe-ui'
import ConversationCard from '@/components/desk/ticket/ConversationCard.vue';
import Conversations from '@/components/desk/ticket/Conversations.vue';
import TopControlPanel from '@/components/desk/ticket/TopControlPanel.vue'
import InfoPanel from '@/components/desk/ticket/InfoPanel.vue';
import ActionPanel from '@/components/desk/ticket/ActionPanel.vue';
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
		ConversationCard,
		Conversations,
		TopControlPanel,
		InfoPanel,
		ActionPanel,
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

		return { 
			editor,
			viewportWidth,
			user,
			tickets,
			ticketController
		}
	},
	resources: {
		submitConversation() {
			return {
				method: 'helpdesk.api.ticket.submit_conversation_via_agent',
				onSuccess: () => {
					// this.$resources.conversations.fetch();
				}
			}
		}
	},
	computed: {
		ticket() {
			return this.tickets[this.ticketId] || null
		}
	},
	methods: {
		startEditing() {
			this.editing = true
			this.delayedConversationScroll()
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
				message: this.content
			})
		},
		getNextTicket() {

		},
		getPreviousTicket() {

		}
	}
}
</script>