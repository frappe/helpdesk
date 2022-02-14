<template>
	<div class="flex">
		<div v-if="ticket" class="sm:w-3/12 px-4">
			<Card title="Contact details">
				<div v-if="contact">
					<hr class="mb-4">
					<div class="text-base space-y-2">
						<div class="flex space-x-2">
							<Avatar class="h-4 w-4" label="John Doe" :imageURL="contact.image" />
							<span class="pt-1">{{ contact.first_name + ' ' + contact.last_name}}</span>
						</div>
						<div class="flex space-x-2">
							<FeatherIcon class="w-6 h-6 mx-1" name="mail" />
							<span class="text-slate-500">{{ contact.email_id }}</span>
						</div>
						<div class="flex space-x-2">
							<FeatherIcon class="w-6 h-6 mx-1" name="phone" />
							<span class="text-slate-500">{{ contact.phone }}</span>
						</div>
					</div>
					<hr class="my-3">
					<div class="text-base space-y-3">
						<span class="text-green-500">Open Tickets (2)</span>
						<div class="space-y-1 text-slate-700">
							<p class="text-slate-500">How to clear payment schedule?</p>
							<p class="text-slate-500">How to bring Helpdesk to FC?</p>
						</div>
					</div>
				</div>
			</Card>
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
		</div>
		<div class="sm:w-3/12">
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
import { Badge, Card, Dropdown, Avatar, FeatherIcon, ListItem} from 'frappe-ui'

export default {
	name: 'TicketConversation',
	inject: ['viewportWidth'],
	props: ['ticketId'],
	components: {
		Badge,
		Card,
		Dropdown,
		Avatar,
		FeatherIcon,
		ListItem
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
		}
	},
	computed: {
		ticket() {
			return this.$resources.ticket.data ? this.$resources.ticket.data : null;
		},
		contact() {
			return this.$resources.contact.data ? this.$resources.contact.data : null;
		}
	},
	methods: {
		toggleDropdown() {
			
		}
	}
}
</script>