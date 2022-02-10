<template>
	<div>
		<div class="sm:py-1 sm:border sm:border-gray-100 sm:rounded-md sm:shadow sm:px-2">
			<div class="block py-2 rounded-md sm:px-2">
				<div class="block py-1 rounded-md sm:px-2">
					<div class="flex items-center justify-between sm:justify-start font-light">
						<div class="mr-4">
							<Input type="checkbox" value="" />
						</div>
						<div class="text-base sm:w-5/12">
							Subject
						</div>
						<div class="text-base sm:w-3/12">
							Requester
						</div> 
						<div class="text-base sm:w-2/12">
							Type
						</div> 
						<div class="text-base sm:w-2/12">
							Status
						</div> 
						<div class="text-base sm:w-3/12">
							Assignee
						</div> 
						<div class="text-base sm:w-2/12">
							Updated
						</div> 
					</div>
				</div>
				<div class="transform translate-y-2 border-b-2"/>
			</div>
			<div
				v-if="this.ticketList"
				class="w-full block overflow-auto"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 15rem)' : null }"
			>
				<div class="flex-auto" v-for="ticket in this.ticketList" :key="ticket">
					<div class="block py-1 rounded-md sm:px-2">
						<TicketListItem :ticketName="ticket" :agents="this.agents"/>
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
	props: ['ticketList', 'agents'],
	components: {
		Input,
		TicketListItem
	},
}
</script>
