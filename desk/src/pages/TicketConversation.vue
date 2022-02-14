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
						v-for="i in [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]" :key="i" 
						class="flex flex-col space-y-4 mt-4 pr-3"
					>
						<ConversationCard 
							userName="Kamal Johnson" 
							profilePicUrl="https://picsum.photos/200" 
							time="5 hrs ago (Feb 2, 2022 11:12 AM)" 
							message="Hey There"
						/>
					</div>
				</div>
				<div class="flex flex-col pr-3">
					<div class="flex">
						<div>
							<Avatar label="John Doe" imageURL="https://picsum.photos/200" />
						</div>
						<div class="grow ml-3">
							<div class="flex justify-between">
								<div class="flex">
									<span class="pt-1">Aditya Hase</span>
								</div>
								<span class="text-slate-500">5 hrs ago (Feb 2, 2022 11:12 AM)</span>
							</div>
							<div class="mt-2">
								<textarea
									class="form-control block w-full px-3 py-1.5 text-base font-normal text-gray-700 bg-slate-50 bg-clip-padding border border-solid border-gray-300 rounded transition ease-in-out m-0 focus:text-gray-700 focus:bg-white focus:border-blue-600 focus:outline-none"
									id="exampleFormControlTextarea1"
									rows="4"
									placeholder="Your message"
								></textarea>
								<div class="my-2">
									<Button>Submit</Button>
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
					<div>
						<hr class="mb-4">
						<div class="mb-4">
							<h3 class="mb-2">Assignee</h3>
							<Dropdown :items="[{ label: 'Option 1' }, { label: 'Option 2' }]" :dropdown-width-full="true">
								<template v-slot="{ toggleDropdown }">
									<Button icon-right="chevron-down" :button-full-width="true" @click="toggleDropdown()">Twinkle Damania</Button>
								</template>
							</Dropdown>
						</div>
						<div class="mb-4">
							<h3 class="mb-2">Type</h3>
							<Dropdown :items="[{ label: 'Option 1' }, { label: 'Option 2' }]" :dropdown-width-full="true">
								<template v-slot="{ toggleDropdown }">
									<Button icon-right="chevron-down" :button-full-width="true" @click="toggleDropdown()">Button</Button>
								</template>
							</Dropdown>
						</div>
						<div class="mb-4">
							<h3 class="mb-2">Status</h3>
							<Dropdown :items="[{ label: 'Option 1' }, { label: 'Option 2' }]" :dropdown-width-full="true">
								<template v-slot="{ toggleDropdown }">
									<Button icon-right="chevron-down" :button-full-width="true" @click="toggleDropdown()">Open</Button>
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
		}
	},
	computed: {
		ticket() {
			return this.$resources.ticket.data ? this.$resources.ticket.data : null;
		},
		contact() {
			return this.$resources.contact.data ? this.$resources.contact.data : null;
		},
		conversations() {
			return this.$resources.conversations.data ? this.$resources.conversations.data : null;
		}
	},
	methods: {
		
	},
	activated() {
		// 
		this.$socket.on('new_message', this.$resources.conversations.fetch());
	},
	deactivated() {
		this.$socket.off('new_message', this.$resources.conversations.fetch());
	},
}
</script>