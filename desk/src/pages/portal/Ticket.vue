<template>
	<div v-if="ticket" class="max-w-4xl mx-auto">
		<div 
			:style="{ height: viewportWidth > 768 ? 'calc(100vh - 9rem)' : null }"
		>
			<div class="flex items-center pb-2 border-b justify-between">
				<div class="text-4xl">
					{{ ticket.subject }}
				</div>
				<div>
					<Button @click="reopenTicket()" appearance="primary" v-if="['Closed', 'Resolved'].includes(ticket.status)">Reopen</Button>
					<Button @click="closeTicket()" appearance="primary" v-else>Close</Button>
				</div>
			</div>
			<div class="grow flex flex-col h-full space-y-2">
				<div class="overflow-auto grow">
					<Conversations :ticketId="ticket.name" :scrollToBottom="scrollConversationsToBottom"/>
				</div>
				<div 
					class="flex flex-col pr-3 pb-3 pt-3" 
				>
					<div class="grow ml-3">
						<div v-if="!(['Closed', 'Resolved'].includes(ticket.status))">
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
								>
									Send
								</Button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
		<!-- <div class="sm:w-4/12">
			<ActionPanel :ticketId="ticket.name" />
		</div> -->
	</div>
</template>

<script>
import { inject, ref } from "vue"
import Conversations from "@/components/portal/ticket/Conversations.vue"
import ActionPanel from "@/components/portal/ticket/ActionPanel.vue"
import '@vueup/vue-quill/dist/vue-quill.snow.css';
import { QuillEditor } from '@vueup/vue-quill'

export default {
    name: "Tickets",
    props: ["ticketId"],
	components: {
		Conversations,
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
		const editor = ref(null)
		const viewportWidth = inject("viewportWidth")
        const tickets = inject("tickets")
        const ticketController = inject("ticketController")
        
		return { editor, viewportWidth, tickets, ticketController }
    },
    computed: {
        ticket() {
			if (this.tickets) {
				return this.tickets[this.ticketId] || null
			}
        }
    },
	resources: {
		submitConversation() {
			return {
				method: 'helpdesk.api.ticket.submit_conversation_via_contact',
				onSuccess: () => {
					// this.$resources.conversations.fetch();
				}
			}
		}
	},
	methods: {
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
		closeTicket() {
			this.ticketController.set(this.ticketId, 'status', 'Closed')
		},
		reopenTicket() {
			this.ticketController.set(this.ticketId, 'status', 'Open')
		}
	}
}
</script>