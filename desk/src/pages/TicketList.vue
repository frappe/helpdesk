<template>
	<div>
		<div>
			<div
				v-if="this.ticketList"
				class="w-full block overflow-auto"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 13rem)' : null }"
			>
				<div class="flex-auto" v-for="ticket in this.ticketList" :key="ticket.name">
					<div class="block px-0">
						<TicketListItem 
							:ticket="ticket"
							:agents="this.agents"
							:types="this.types"
							:statuses="this.statuses"
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from 'frappe-ui'
import TicketListItem from '../components/TicketListItem.vue'

export default {
	name: 'TicketList',
	inject: ['viewportWidth'],
	props: ['ticketList', 'agents', 'types', 'statuses'],
	components: {
		Input,
		TicketListItem
	},
}
</script>
