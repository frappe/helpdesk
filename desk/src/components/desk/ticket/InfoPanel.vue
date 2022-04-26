<template>
	<div class="pt-[15px]" v-if="ticket">
		<div class="text-base border-b pl-[15px] pr-[25.33px] pb-[14px]">
			<LoadingText v-if="updatingContact"/>
			<div v-else>
				<div v-if="!editingContact">
					<div v-if="ticket.contact" class="space-y-[12px]">
						<div class="flex flex-row items-center space-x-[6px]">
							<div class="w-7">
								<CustomAvatar :label="contactFullName" :imageURL="ticket.contact.image" size="md" />
							</div>
							<div class="grow truncate font-semibold text-base">{{ contactFullName }}</div>
							<div class="flex">
								<FeatherIcon 
									name="edit-2" 
									class="stroke-slate-400 w-4 h-4 cursor-pointer"
									@click="() => {editingContact=!editingContact}"
								/>
							</div>
						</div>
						<div v-if="ticket.contact.phone_nos.length > 0" class="flex space-x-[6px] items-center">
							<div class="w-7 px-[6.5px]">
								<FeatherIcon name="phone" class="stroke-gray-500" style="width: 15px;" />
							</div>
							<div class="space-y-1" v-for="phone_no in ticket.contact.phone_nos" :key="phone_no">
								<div class="text-gray-700 text-base">{{ phone_no.phone }}</div>
							</div>
						</div>
						<div v-if="ticket.contact.email_ids.length > 0" class="flex space-x-[6px] items-center">
							<div class="w-7 px-[6.5px]">
								<FeatherIcon name="mail" class="stroke-gray-500" style="width: 15px;" />
							</div>
							<div class="space-y-1 max-w-[153px]" v-for="email_id in ticket.contact.email_ids" :key="email_id">
								<div class="truncate text-gray-700 text-base">{{ email_id.email_id }}</div>
							</div>
						</div>
					</div>
					<div v-else>
						<div v-if="!updatingContact" class="flex flex-row-reverse">
							<FeatherIcon 
								name="edit-2" 
								class="stroke-slate-400 w-4 h-4 cursor-pointer"
								@click="() => {editingContact=!editingContact}"
							/>
						</div>
					</div>
				</div>
				<div v-else class="w-full">
					<div class="flex space-x-2 mb-2">
						<div class="grow">Select Contact</div>
						<FeatherIcon 
							name="x" 
							class="stroke-slate-400 w-4 h-4 cursor-pointer hover:stroke-red-500"
							@click="() => {editingContact=!editingContact}"
						/>
					</div>
					<Combobox v-model="selectedContact">
						<ComboboxInput 
							class="rounded-md w-full border-none focus:ring-0 py-2 pl-3 pr-10 text-sm leading-5 text-gray-900 bg-slate-100"
							autocomplete="off"
							@change="query = $event.target.value" 
						/>
						<ComboboxOptions
							class="w-full py-1 mt-1 overflow-auto text-base bg-white rounded-md shadow-lg max-h-60 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
						>
							<div
								v-if="filterdContacts.length === 0 && query !== ''"
								class="select-none relative py-2 px-4 text-gray-700 cursor-pointer"
								@click="() => {showNewContactDialog = true}"
							>
								Create new
							</div>
							<ComboboxOption
								v-slot="{ selected, active }"
								v-for="contactItem in filterdContacts" :key="contactItem"
								:value="contactItem.name"
							>
								<li
									class="cursor-default select-none relative py-2 pl-4 pr-4 text-gray-900"
									:class="{'bg-slate-50': active}"
								>
									<span
										class="block truncate"
										:class="{ 'font-medium': selected, 'font-normal': !selected }"
										>
										{{ contactItem.name }}
									</span>
								</li>
							</ComboboxOption>
						</ComboboxOptions>
					</Combobox>
				</div>
			</div>
		</div>
		<div>
			<div class="border-b py-[14px] pl-[19px] pr-[27.81px] space-y-1 select-none" v-if="otherTicketsOfContact && !editingContact">
				<div class="flex flex-row items-center" :class="otherTicketsOfContact.length > 0 ? 'cursor-pointer' : ''" @click="() => {showOtherTicketsOfContacts = !showOtherTicketsOfContacts}">
					<div class="grow text-base font-semibold"> Open Tickets </div>
					<CustomIcons v-if="otherTicketsOfContact.length > 0" class="h-[6px] fill-gray-400" :name="showOtherTicketsOfContacts ? 'chevron-up' : 'chevron-down'"  />
				</div>
				<div v-if="showOtherTicketsOfContacts" class="max-h-[200px] overflow-scroll pt-[7px]">
					<div v-for="ticket in otherTicketsOfContact" :key="ticket.name">
						<router-link :to="`/frappedesk/tickets/${ticket.name}`" class="text-slate-500 text-base">
							<div class="py-1 hover:bg-slate-50 rounded max-w-[200px]">
								<div class="text-slate-500 truncate">{{ ticket.subject }}</div>
							</div>
						</router-link>
					</div>
				</div>
			</div>
			<div class="border-b py-[14px] pl-[19px] pr-[27.81px] space-y-1 select-none" v-if="otherTicketsOfContact && !editingContact">
				<div class="flex flex-row items-center" :class="otherTicketsOfContact.length > 0 ? 'cursor-pointer' : ''" @click="() => {showTicketHistory = !showTicketHistory}">
					<div class="grow text-base font-semibold"> Ticket History </div>
					<CustomIcons v-if="otherTicketsOfContact.length > 0" class="h-[6px] fill-gray-400" :name="showTicketHistory ? 'chevron-up' : 'chevron-down'"  />
				</div>
				<div v-if="showTicketHistory" class="max-h-[200px] overflow-scroll pt-[7px]">
					<div v-for="(activity, index) in activities" :key="activity.name">
						<ActivityCard :activity="activity" :isLast="index == activities.length - 1" />
					</div>
				</div>
			</div>
		</div>
		<NewContactDialog v-model="showNewContactDialog" @contact-created="(contact) => {contactCreated(contact)}"/>
	</div>
</template>

<script>
import { FeatherIcon, Input, LoadingText } from 'frappe-ui'
import CustomAvatar from '@/components/global/CustomAvatar.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import ActivityCard from '@/components/desk/ticket/ActivityCard.vue'
import {
	Combobox,
	ComboboxInput,
	ComboboxOptions,
	ComboboxOption,
} from '@headlessui/vue'
import NewContactDialog from '@/components/desk/global/NewContactDialog.vue'
import { inject, ref } from 'vue'

export default {
	name: "InfoPanel",
	props: ["ticketId"],
	components: {
		FeatherIcon,
		Input,
		LoadingText,
		CustomAvatar,
		CustomIcons,
		ActivityCard,
		Combobox,
		ComboboxInput,
		ComboboxOption,
		ComboboxOptions,
		NewContactDialog
	},
	setup() {
		const editingContact = ref(false)
		const updatingContact = ref(false)
		const contactName = ref('')
		const selectedContact = ref('')
		const query = ref('')

		const showNewContactDialog = ref(false)
		const showTicketHistory = ref(false)

		const tickets = inject('tickets')
		const contacts = inject('contacts')
		const ticketController = inject('ticketController')

		const showOtherTicketsOfContacts = ref(false)

		return {
			editingContact,
			updatingContact,
			contactName,
			selectedContact,
			query,
			showNewContactDialog,
			showTicketHistory,
			tickets,
			contacts,
			ticketController,
			showOtherTicketsOfContacts
		}
	},
	computed: {
		ticket() {
			return this.tickets[this.ticketId] || null
		},
		contactFullName() {
			if (this.ticket.contact) {
				return ((this.ticket.contact.first_name || "") + " " + (this.ticket.contact.last_name || "")).slice(0, 40)
			}
		},
		filterdContacts() {
			return this.query === ''
				? this.contacts
				: this.contacts.filter((contactItem) => {
					return contactItem.name.toLowerCase().includes(this.query.toLowerCase())
				})
		},
		otherTicketsOfContact() {
			return this.$resources.otherTicketsOfContact.data || null
		},
		activities() {
			return this.$resources.activities.data || null;
		},
	},
	watch: {
		selectedContact(newValue) {
			if (newValue) {
				this.updateContact()
			}
		}
	},
	methods: {
		updateContact() {
			this.editingContact = false
			this.updatingContact = true
			this.ticketController.set(this.ticketId, 'contact', this.selectedContact).then(() => {
				this.selectedContact = ''
				this.query = ''
				this.updatingContact = false
				this.$resources.otherTicketsOfContact.fetch()
			})
		},
		contactCreated(contact) {
			this.showNewContactDialog = false
			this.editingContact = false
			this.ticketController.set(this.ticketId, 'contact', contact.name)
		}
	},
	resources: {
		otherTicketsOfContact() {
			return {
				method: 'frappedesk.api.ticket.get_other_tickets_of_contact',
				params: {
					ticket_id: this.ticketId
				},
				auto: true
			}
		},
		activities() {
			return {
				method: 'frappedesk.api.ticket.activities',
				params: {
					name: this.ticketId
				},
				auto: true
			}
		}
	}
}
</script>

<style>

</style>