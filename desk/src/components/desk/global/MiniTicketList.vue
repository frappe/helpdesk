<template>
	<div class="flex flex-col space-y-2 p-3 pr-0" v-if="manager">
		<div v-if="!manager.loading">
			<div v-if="manager.list.length > 0">
				<div v-for="ticket in manager.list" :key="ticket.name">
					<router-link
						:to="`/frappedesk/tickets/${ticket.name}`"
						:style="
							['Closed', 'Resolved'].includes(ticket.status)
								? 'opacity: 0.5;'
								: ''
						"
						class="flex flex-row group items-center text-base select-none rounded-[6px] py-[7px] pl-[9px] hover:bg-gray-50 space-x-[12px] max-w-full"
					>
						<div
							class="text-gray-600 font-normal shrink-0"
							:style="
								['Closed', 'Resolved'].includes(ticket.status)
									? 'opacity: 0.5;'
									: ''
							"
						>
							{{ ticket.name }}
						</div>
						<a
							:title="ticket.subject"
							class="shrink"
							:class="size ? `sm:max-w-${size}` : 'sm:max-w-sm'"
						>
							<p
								class="truncate"
								:class="
									!seenTicket(ticket)
										? 'font-semibold text-gray-800'
										: ['Closed', 'Resolved'].includes(
												ticket.status
										  )
										? 'font-normal text-gray-600'
										: 'font-normal text-gray-900'
								"
							>
								{{ ticket.subject }}
							</p>
						</a>
						<a
							:title="ticket.ticket_type"
							v-if="ticket.ticket_type"
							class="shrink max-w-[80px] text-gray-600 font-medium bg-gray-200 px-[8px] py-[2px] rounded-[48px] uppercase text-xs"
						>
							<p class="truncate">
								{{ ticket.ticket_type }}
							</p>
						</a>
					</router-link>
				</div>
			</div>
			<div v-else>
				<div class="grid place-content-center h-48 w-full">
					<div>
						<CustomIcons
							name="empty-list"
							class="h-12 w-12 mx-auto mb-2"
						/>
						<div class="text-gray-500 mb-2">No tickets found</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { inject } from "vue"
import CustomIcons from "./CustomIcons.vue"

export default {
	name: "MiniTicketlist",
	props: ["manager", "size"],
	components: {
		CustomIcons,
	},
	setup() {
		const user = inject("user")
		return {
			user,
		}
	},
	methods: {
		seenTicket(ticket) {
			let seenFlag = false
			if (ticket._seen) {
				JSON.parse(ticket._seen).forEach((seen) => {
					if (seen === this.user.user) {
						seenFlag = true
					}
				})
			}
			return seenFlag
		},
	},
}
</script>

<style></style>
