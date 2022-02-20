<template>
	<div>
		<div>
			<div
				v-if="this.tickets"
				class="w-full block overflow-auto"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.3rem)' : null }"
			>
				<div class="flex-auto" v-for="ticket in tickets" :key="ticket.name">
					<div class="block px-0">
						<TicketListItem :ticket="ticket" />
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from 'frappe-ui'
import TicketListItem from './TicketListItem.vue'

export default {
	name: 'TicketList',
	inject: ['viewportWidth'],
	props: ['tickets'],
	components: {
		Input,
		TicketListItem
	},
	computed: {
		tickets() {
			return this.$tickets().get({filter: this.$ticketFilter.get()});
		}
	}
}
</script>
