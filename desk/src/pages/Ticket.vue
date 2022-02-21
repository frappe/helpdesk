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
						<Conversations :ticket="ticket" />
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
		getNextTicket() {

		},
		getPreviousTicket() {

		}
	}
}
</script>