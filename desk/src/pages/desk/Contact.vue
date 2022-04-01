<template>
	<div>
		<div v-if="!$resources.contact.loading && contact">
			<div class="flex py-3 border-b items-center text-base pl-4 pr-8">
				<div class="grow">
					<div class="flex items-center">
						<div class="sm:w-3/12 truncate pr-10">
						{{ fullName }}
						</div>
						<div class="sm:w-3/12">
							<div v-if="email" class="flex items-center space-x-2">
								<div class="w-[1.1rem]">
									<FeatherIcon name="mail" class="w-4 h-4" />
								</div>
								<div class="truncate pr-10">
									{{ email }}
								</div>
							</div>
						</div>
						<div class="sm:w-3/12">
							<div v-if="phone" class="flex items-center space-x-2">
								<div class="w-[1.1rem]">
									<FeatherIcon name="phone" class="w-4 h-4" />
								</div>
								<div class="truncate pr-10">
									{{ phone }}
								</div>
							</div>
						</div>
					</div>
				</div>
				<div class="flex items-center space-x-2">
					<Button>Edit Details</Button>
				</div>
			</div>
			<div class="pt-4">
				<div class="mb-4 ml-4 font-semibold text-xl"> Tickets </div>
				<TicketList :sortby="ticketsSortby" :sortDirection="ticketSsortDirection" :filters="ticketsFilters" @selected-tickets-on-change="() => {}" />
			</div>
		</div>
		<div v-else class="p-5">
			<LoadingText text="Fetching contact details..." />
		</div>
	</div>
</template>

<script>
import TicketList from "@/components/desk/tickets/TicketList.vue"
import { LoadingText, FeatherIcon } from 'frappe-ui'
import { ref } from 'vue'
import router from '@/router';

export default {
	name: 'Contact',
	props: ['contactId'],
	components: {
		TicketList,
		LoadingText,
		FeatherIcon
	},
	setup(props) {
		const ticketsSortby = ref('modified')
		const ticketsSortDirection = ref('dessending')
		const ticketsFilters = ref([{ raised_by: props.contactId }])

		return {
			ticketsSortby,
			ticketsSortDirection,
			ticketsFilters
		}
	},
	resources: {
		contact() {
			return {
				method: 'frappe.client.get',
				params: {
					doctype: 'Contact',
					name: this.contactId,
					fields: ["*"]
				},
				onSuccess: (data) => {
					console.log(data)
				},
				auto: true
			}
		}
	},
	computed: {
		contact() {
			return this.$resources.contact.data || null
		},
		fullName() {
			if (this.contact) {
				return (this.contact.first_name || "") + " " + (this.contact.last_name || "")
			}
		},
		email() {
			if (this.contact) {
				if (this.contact.email_ids && this.contact.email_ids.length > 0) {
					return this.contact.email_ids[0].email_id
				} else if (this.contact.email_id) {
					return this.contact.email_id
				}
			}
		},
		phone() {
			if (this.contact) {
				if (this.contact.phone_nos && this.contact.phone_nos.length > 0) {
					return this.contact.phone_nos[0].phone
				} else if (this.contact.phone) {
					return this.contact.phone
				}
			}
		}
	},
}
</script>

<style>

</style>