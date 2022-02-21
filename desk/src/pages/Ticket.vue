<template>
	<div v-if="ticket">
		<TopControlPanel :ticket="ticket" @next="getNextTicket" @previous="getPreviousTicket"/>
		<div class="flex">
			<div 
				class="w-60 border-r"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.5rem)' : null }"
			>
				<InfoPanel :ticket="ticket" :contact="contact" />
			</div>
			<div
				class="grow pt-4 px-4"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 10rem)' : null }"
			>
				<div class="flex items-center">
					<span class="text-6xl">
						{{ ticket.name }} - {{ ticket.subject }}
					</span>
					<Badge color="green" class="ml-3 align-middle">{{ ticket.status }}</Badge>
				</div>
				<div class="flex flex-col h-full space-y-2">
					<div class="overflow-auto grow">
						<div
							:v-if="conversations"
							v-for="(conversation, index) in conversations" :key="conversation.name" 
							class="flex flex-col space-y-4 mt-4 pr-3"
							ref="conversationContainer"
						>
							<div :ref="`conversation-${index}`">
								<ConversationCard 
									:userName="(conversation.sender.first_name ? conversation.sender.first_name : '') + (conversation.sender.last_name ? conversation.sender.last_name : '')" 
									:profilePicUrl="conversation.sender.image ? conversation.sender.image : ''" 
									:time="conversation.creation" 
									:message="conversation.content"
								/>
							</div>
						</div>
					</div>
					<div class="flex flex-col pr-3">
						<div class="flex">
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
									<textarea
										class="form-control block w-full px-3 py-1.5 text-base font-normal text-gray-700 bg-slate-50 bg-clip-padding border border-solid border-gray-300 rounded transition ease-in-out m-0 focus:text-gray-700 focus:bg-white focus:border-blue-600 focus:outline-none"
										id="exampleFormControlTextarea1"
										rows="4"
										:placeholder="sessionAgent ? 'Reply to ' + contact.first_name : 'Only agents can reply to tickets'"
										v-model="this.currentConversationText"
										:disabled="!sessionAgent"
									></textarea>
									<div class="my-2">
										<Button :loading="this.$resources.submitConversation.loading" @click="this.submitConversation" :disabled="!sessionAgent">Submit</Button>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<div 
				class="w-60 border-l"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.5rem)' : null }"
			>
				<ActionPanel :ticket="ticket" />
			</div>
		</div>
	</div>
</template>
<script>
import { Badge, Card, Dropdown, Avatar } from 'frappe-ui'
import ContactCard from '../components/ticket/ContactCard.vue';
import ConversationCard from '../components/ticket/ConversationCard.vue';
import TopControlPanel from '../components/ticket/TopControlPanel.vue'
import InfoPanel from '../components/ticket/InfoPanel.vue';
import ActionPanel from '../components/ticket/ActionPanel.vue';

export default {
	name: 'Ticket',
	inject: ['viewportWidth'],
	props: ['ticketId'],
	components: {
    Badge,
    Card,
    Dropdown,
    ContactCard,
    Avatar,
    ConversationCard,
    TopControlPanel,
    InfoPanel,
    ActionPanel
},
	data() {
		return {
			currentConversationText: '',
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
		conversations() {
			return {
				method: 'helpdesk.api.ticket.get_conversations',
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
					this.$resources.conversations.fetch();
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
		conversations() {
			this.$nextTick(() => {
				this.autoScrollToBottom();
			})
			return this.$resources.conversations.data || null;
		}
	},
	activated() {
		this.$socket.on('list_update', (data) => {
			if (data['doctype'] == 'Ticket' && data['name'] == this.ticketId) {
				this.$resources.conversations.fetch()
			}
		});
	},
	deactivated() {
		this.$socket.off('list_update');
	},
	methods: {
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.$agents.get()) {
				this.$agents.get().forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$tickets(this.ticket.name).assignAgent(agent.name)
						},
					});
				});
				let options = [];
				if (this.$user.get().agent) {
					options.push({
						group: 'Myself',
						hideLabel: true,
						items: [
							{
								label: 'Assign to me',
								handler: () => {
									this.$tickets(this.ticket.name).assignAgent()
								}
							},
						],
					})
				}
				options.push({
					group: 'All Agents',
					hideLabel: true,
					items: agentItems,
				})
				return options;
			} else {
				return null;
			}
		},
		typesAsDropdownOptions() {
			let typeItems = [];
			if (this.$tickets().get("types")) {
				this.$tickets().get("types").forEach(type => {
					typeItems.push({
						label: type,
						handler: () => {
							this.$tickets(this.ticket.name).assignType(type)
						},
					});
				});
				return typeItems;
			} else {
				return null;
			}
		},
		statusesAsDropdownOptions() {
			let statusItems = [];
			if (this.$tickets().get("statuses")) {
				this.$tickets().get("statuses").forEach(status => {
					statusItems.push({
						label: status,
						handler: () => {
							this.$tickets(this.ticket.name).assignStatus(status)
						},
					});
				});
				return statusItems;
			} else {
				return null;
			}
		},
		submitConversation() {
			this.$resources.submitConversation.submit({
				ticket_id: this.ticketId,
				message: this.currentConversationText
			})
			this.currentConversationText = ""
		},
		autoScrollToBottom() {
			if (this.conversations) {
				const [el] = this.$refs["conversation-" + (this.conversations.length - 1)];
				if (el) {
					el.scrollIntoView({behavior: 'smooth'});
				}
			}
		},
		getNextTicket() {

		},
		getPreviousTicket() {

		}
	}
}
</script>