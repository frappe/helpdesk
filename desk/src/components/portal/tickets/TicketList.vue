<template>
	<div class="px-3 bg-white border rounded-lg shadow">
		<div class="px-1">
			<div class="flex items-center border-b py-4 text-gray-500">
				<div class="sm:w-8/12">
					<div class="cursor-pointer w-fit hover:text-gray-700" @click="changeSortBy('subject')">
						<div class="flex items-center space-x-1">
							<div> Subject </div>
							<FeatherIcon v-if="sortBy == 'subject'" :name="sortAscending ? 'arrow-up' : 'arrow-down'" class="w-4 h-4"/>
						</div>
					</div>
				</div>
				<div class="sm:w-2/12">
					<div class="cursor-pointer w-fit hover:text-gray-700" @click="changeSortBy('status')">
						<div class="flex items-center space-x-1">
							<div> Status </div>
							<FeatherIcon v-if="sortBy == 'status'" :name="sortAscending ? 'arrow-up' : 'arrow-down'" class="w-4 h-4"/>
						</div>
					</div>
				</div>
				<div class="sm:w-2/12 flow-root">
					<div class="float-right cursor-pointer w-fit hover:text-gray-700" @click="changeSortBy('creation')">
						<div class="flex items-center space-x-1">
							<FeatherIcon v-if="sortBy == 'creation'" :name="sortAscending ? 'arrow-up' : 'arrow-down'" class="w-4 h-4"/>
							<div> Created </div>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div v-for="(ticket, key, index) in tickets" :key="ticket.name" class="space-y-4">
			<router-link :to="`/support/tickets/${ticket.name}`">
				<div class="px-1 rounded hover:bg-slate-50 cursor-pointer">
					<div class="flex items-center py-4" :class="index < Object.keys(tickets).length - 1 ? 'border-b' : ''">
						<div class="sm:w-8/12 flex space-x-2 pr-2">
							<div class="truncate">{{ ticket.subject }}</div>
							<div>{{ `#${ticket.name}` }}</div>
						</div>
						<div class="sm:w-2/12">
							<Badge :color="getStatusBadgeColor(ticket.status)">{{ getStatus(ticket.status) }}</Badge>
						</div>
						<div class="sm:w-2/12 flow-root">
							<div class="float-right text-slate-500">{{ formatedCreationTime(ticket.creation) }}</div>
						</div>
					</div>
				</div>
			</router-link>
		</div>
	</div>
</template>

<script>
import { inject, ref  } from "vue"
import { Badge, FeatherIcon } from 'frappe-ui'

export default {
	name: 'TicketList',
	components: {
		Badge,
		FeatherIcon
	},
	setup() {
		const tickets = inject('tickets')
		const sortBy = ref('creation')
		const sortAscending = ref(false)

		return { tickets, sortBy, sortAscending }
	},
	computed: {
		tickets() {
			if (this.tickets) {
				this.tickets = Object.values(this.tickets).sort((a,b) => (a[this.sortBy] > b[this.sortBy]) ? 1 : ((b[this.sortBy] > a[this.sortBy]) ? -1 : 0))
				if (!this.sortAscending) {
					this.tickets.reverse()
				}
				return this.tickets;
			}
			return null
		}
	},
	methods: {
		getStatus(status) {
			switch(status) {
				case 'Replied':
					return 'Waiting For Reply'
				case 'Resolved':
					return 'Closed'
				default:
					return status
			}
		},
		getStatusBadgeColor(status) {
			switch(status) {
				case 'Replied':
					return 'yellow'
				case 'Resolved':
					return 'green'
				case 'On Hold':
					return 'blue'
				case 'Closed':
					return 'green'
				case 'Open':
					return 'red'
			}
		},
		formatedCreationTime(time) {
			let formatedTime = this.$dayjs(time).fromNow()
			return formatedTime === 'Now' ? 'Just now' : formatedTime + ' ago'
		},
		changeSortBy(fieldname) {
			if (this.sortBy == fieldname) {
				this.sortAscending = !this.sortAscending
			} else {
				this.sortBy = fieldname 
				this.sortAscending = true
			}
		}
	}
}
</script>

<style>

</style>