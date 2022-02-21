<template>
	<div v-if="ticket">
		<TopControlPanel :ticket="ticket" @next="getNextTicket" @previous="getPreviousTicket"/>
		<div class="flex">
			<div 
				class="w-1/5 border-r"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.5rem)' : null }"
			>
				<InfoPanel :ticket="ticket" :contact="contact" />
			</div>
			<div
				class="w-3/5 pt-3 px-4"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 10.5rem)' : null }"
			>
				<div class="flex items-center pb-4">
					<span class="text-4xl">
						{{ ticket.name }} - {{ ticket.subject }}
					</span>
				</div>
				<div class="flex flex-col h-full space-y-2">
					<div class="overflow-auto grow">
						<Conversations :ticket="ticket" :scrollToBottom="scrollConversationsToBottom"/>
					</div>
					<div class="flex flex-col pr-3 pb-10">
						<div class="flex" v-if="editing">
							<div v-if="sessionAgent">
								<Avatar label="John Doe" :imageURL="sessionAgent.image" />
							</div>
							<div class="grow ml-3">
								<div class="flex justify-between">
									<div class="flex" v-if="sessionAgent">
										<span class="pt-1">{{ sessionAgent.agent_name }}</span>
									</div>
								</div>
								<div class="mt-2" v-if="contact">
									<QuillEditor v-model:content="content" theme="snow" toolbar="full" contentType="html"/>
									<div class="mt-2 space-x-2">
										<Button :loading="this.$resources.submitConversation.loading" @click="this.submitConversation" appearance="primary" :disabled="!sessionAgent">Submit</Button>
										<Button appearance="secondary" @click="cancelEditing()">Cancel</Button>
									</div>
								</div>
							</div>
						</div>
						<div class="flex space-x-2 pt-3" v-else>
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
				<ActionPanel :ticket="ticket" :contact="contact" />
			</div>
		</div>
	</div>
</template>
<script>
import { Badge, Card, Dropdown, Avatar } from 'frappe-ui'
import ConversationCard from '../components/ticket/ConversationCard.vue';
import Conversations from '../components/ticket/Conversations.vue';
import TopControlPanel from '../components/ticket/TopControlPanel.vue'
import InfoPanel from '../components/ticket/InfoPanel.vue';
import ActionPanel from '../components/ticket/ActionPanel.vue';
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css';

export default {
	name: 'Ticket',
	inject: ['viewportWidth'],
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
			content: ""
		}
	},
	resources: {
		sessionAgent() {
			return {
				method: 'helpdesk.api.agent.get_session_agent',
				auto: true
			}
		},
		contact() {
			return {
				method: 'helpdesk.api.ticket.get_contact',
				params: {
					ticket_id: this.ticketId
				},
				auto: true
			}
		},
		submitConversation() {
			return {
				method: 'helpdesk.api.ticket.submit_conversation',
				onSuccess: () => {
					// this.$resources.conversations.fetch();
				}
			}
		}
	},
	computed: {
		ticket() {
			return this.$tickets(this.ticketId).get()
		},
		sessionAgent() {
			return this.$resources.sessionAgent.data || null;
		},
		contact() {
			return this.$resources.contact.data || null;
		},
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
			console.log(`content: ${this.content}`);
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