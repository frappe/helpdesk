<template>
	<div class="flex">
		<div v-if="ticket" class="sm:w-3/12 px-4">
			<ContactCard v-if="contact" :contact="contact" />
		</div>
		<div
			v-if="ticket"
			class="sm:w-9/12 px-4"
			:style="{ height: viewportWidth > 768 ? 'calc(100vh - 8rem)' : null }"
		>
			<div class="flex">
				<div class="text-6xl">
					{{ ticket.name }} - {{ ticket.subject }}
				</div>
				<Badge color="green" class="my-2 ml-3">{{ ticket.status }}</Badge>
			</div>
			<div class="flex flex-col h-full space-y-2">
				<div class="overflow-auto grow">
					<div
						:v-if="conversations"
						v-for="conversation in conversations" :key="conversation.name" 
						class="flex flex-col space-y-4 mt-4 pr-3"
					>
						<ConversationCard 
							:userName="(conversation.sender.first_name ? conversation.sender.first_name : '') + (conversation.sender.last_name ? conversation.sender.last_name : '')" 
							:profilePicUrl="conversation.sender.image ? conversation.sender.image : ''" 
							:time="conversation.creation" 
							:message="conversation.content"
						/>
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
									<Button @click="this.submitConversation" :disabled="!sessionAgent">Submit</Button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div class="sm:w-3/12 pl-3">
			<div v-if="ticket">
				<Card :title="'Ticket #' + ticket.name">
					<div class="px-1">
						<hr class="mb-4">
						<div class="mb-4">
							<h3 class="mb-2" v-if="agents">Assignee</h3>
							<Dropdown 
								:options="agentsAsDropdownOptions()" 
								:dropdown-width-full="true" 
								placement="left"
							>
								<template v-slot="{ toggleDropdown }">
									<Button icon-right="chevron-down" :button-full-width="true" @click="toggleDropdown">
										<div v-if="ticket.assignees">{{ ticket.assignees[0].agent_name }}</div>
										<div v-else></div>
									</Button>
								</template>
							</Dropdown>
						</div>
						<div class="mb-4">
							<h3 class="mb-2">Type</h3>
							<Dropdown 
								:options="typesAsDropdownOptions()" 
								:dropdown-width-full="true"
								placement="left"	
							>
								<template v-slot="{ toggleDropdown }">
									<Button icon-right="chevron-down" :button-full-width="true" @click="toggleDropdown">{{ ticket.ticket_type }}</Button>
								</template>
							</Dropdown>
						</div>
						<div class="mb-4">
							<h3 class="mb-2">Status</h3>
							<Dropdown 
								:options="statusesAsDropdownOptions()" 
								:dropdown-width-full="true"
								placement="left"
							>
								<template v-slot="{ toggleDropdown }">
									<Button icon-right="chevron-down" :button-full-width="true" @click="toggleDropdown">{{ ticket.status }}</Button>
								</template>
							</Dropdown>
						</div>
						<div class="mb-4">
							<h3 class="mb-2">Team</h3>
							<Dropdown :items="[{ label: 'Option 1' }, { label: 'Option 2' }]" :dropdown-width-full="true">
								<template v-slot="{ toggleDropdown }">
									<Button icon-right="chevron-down" :button-full-width="true" @click="toggleDropdown()">Functional</Button>
								</template>
							</Dropdown>
						</div>
					</div>
				</Card>
			</div>
		</div>
	</div>
</template>
<script>
import { Badge, Card, Dropdown, Avatar } from 'frappe-ui'
import ContactCard from '../components/ContactCard.vue';
import ConversationCard from '../components/ConversationCard.vue';

export default {
	name: 'TicketConversation',
	inject: ['viewportWidth'],
	props: ['ticketId'],
	components: {
		Badge,
		Card,
		Dropdown,
		ContactCard,
		Avatar,
		ConversationCard
	},
	data() {
		return {
			currentConversationText: '',
		}
	},
	resources: {
		ticket() {
			return {
				method: 'helpdesk.api.ticket.get_ticket',
				params: {
					ticket_id: this.ticketId
				},
				auto: true
			}
		},
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
		agents() {
			return {
				method: 'helpdesk.api.agent.get_all',
				auto: true
			}
		},
		assignTicketToAgent() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_to_agent',
				debounce: 300,
				onSuccess: () => {
					this.$resources.ticket.fetch();
				}
			}
		},
		assignTicketType() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_type',
				debounce: 300,
				onSuccess: () => {
					this.$resources.ticket.fetch();
				}
			}
		},
		assignTicketStatus() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_status',
				debounce: 300,
				onSuccess: () => {
					this.$resources.ticket.fetch();
				}
			}
		},
		types() {
			return {
				method: 'helpdesk.api.ticket.get_all_ticket_types',
				auto: true
			}
		},
		statuses() {
			return {
				method: 'helpdesk.api.ticket.get_all_ticket_statuses',
				auto: true
			}
		},
		submitConversation() {
			return {
				method: 'helpdesk.api.ticket.submit_conversation',
				debounce: 300,
				onSuccess: () => {

				}
			}
		}
	},
	computed: {
		ticket() {
			return this.$resources.ticket.data ? this.$resources.ticket.data : null;
		},
		sessionAgent() {
			return this.$resources.sessionAgent.data ? this.$resources.sessionAgent.data : null;
		},
		contact() {
			return this.$resources.contact.data ? this.$resources.contact.data : null;
		},
		conversations() {
			return this.$resources.conversations.data ? this.$resources.conversations.data : null;
		},
		agents() {
			return this.$resources.agents.data ? this.$resources.agents.data : null;
		},
		types() {
			return this.$resources.types.data ? this.$resources.types.data : null
		},
		statuses() {
			return this.$resources.statuses.data ? this.$resources.statuses.data : null;
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
			if (this.agents) {
				this.agents.forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$resources.assignTicketToAgent.submit({
								ticket_id: this.ticket.name,
								agent_id: agent.name
							});
						},
					});
				});
				let options = [
					{
						group: 'Actions',
						hideLabel: true,
						items: [
							{
								label: 'Assign to me',
								handler: () => {
									this.$resources.assignTicketToAgent.submit({
										ticket_id: this.ticket.name
									});
								}
							},
						],
					},
					{
						items: agentItems,
					}
				];
				return options;
			} else {
				return null;
			}
		},
		typesAsDropdownOptions() {
			let typeItems = [];
			if (this.types) {
				this.types.forEach(type => {
					typeItems.push({
						label: type,
						handler: () => {
							this.$resources.assignTicketType.submit({
								ticket_id: this.ticket.name,
								type: type
							});
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
			if (this.statuses) {
				this.statuses.forEach(status => {
					statusItems.push({
						label: status,
						handler: () => {
							this.$resources.assignTicketStatus.submit({
								ticket_id: this.ticket.name,
								status: status
							});
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
		}
	}
}
</script>