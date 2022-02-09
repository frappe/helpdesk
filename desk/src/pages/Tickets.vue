<template>
	<div>
		<div>
			<div class="flow-root mb-2">
				<p class="float-left text-6xl font-bold"> Tickets </p>
				<div class="float-right mb-4">
					<div class="flex space-x-3">
						<Button icon-left="filter">Add Filter</Button>
						<Button icon-left="plus">Last Modified</Button>
						<Button icon-left="plus" type="primary">Add Ticket</Button>
					</div>
				</div>
			</div>
			<TicketList />
		</div>
	</div>
</template>
<script>
import TicketList from './TicketList.vue'

export default {
	name: 'Tickets',
	inject: ['viewportWidth'],
	components: {
		TicketList
	}
}
</script>
