<template>
	<div class="flex">
		<div class="sm:w-3/12 px-4 space-y-5">
			<div>
				<Card title="Contact details">
					<div>
						<hr class="mb-4">
						<div class="text-base">Card content</div>
					</div>
				</Card>
			</div>
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
	</div>
</template>
<script>
import { Badge } from 'frappe-ui'
import { Card } from 'frappe-ui'
import { Dropdown } from 'frappe-ui'

export default {
	name: 'TicketConversation',
	inject: ['viewportWidth'],
	props: ['ticketId'],
	components: {
		Badge,
		Card,
		Dropdown
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
	},
	computed: {
		ticket() {
			return this.$resources.ticket.data;
		}
	},
	methods: {
		toggleDropdown() {
			
		}
	}
}
</script>