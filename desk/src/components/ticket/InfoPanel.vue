<template>
	<div class="px-3" v-if="contact && ticket">
		<div class="py-4 space-y-3 text-base">
			<div class="flex items-center">
				<div class="grow text-lg font-medium">{{ `Contact Information ${editing ? "(editing)" : ""}` }}</div>
				<FeatherIcon 
					:name="editing ? 'x' : 'edit-2'" 
					class="stroke-slate-400 w-4 h-4 cursor-pointer" 
					@click="() => {editing=!editing}"
				/>
			</div>
			<div v-if="!editing" class="space-y-2">
				<div class="flex space-x-2">
					<FeatherIcon name="user" class="w-4 h-4" />
					<div class="text-slate-500 truncate">{{ contactFullName }}</div>
				</div>
				<div class="flex space-x-2">
					<FeatherIcon name="mail" class="w-4 h-4" />
					<div>
						<div class="space-y-1" v-for="email_id in contact.email_ids" :key="email_id">
							<div class="text-slate-500 truncate">{{ email_id.email_id }}</div>
						</div>
					</div>
				</div>
				<div v-if="contact.phone_nos.length > 0" class="flex space-x-2">
					<FeatherIcon name="phone" class="w-4 h-4" />
					<div>
						<div class="space-y-1" v-for="phone_no in contact.phone_nos" :key="phone_no">
							<div class="text-slate-500 truncate">{{ phone_no.phone }}</div>
						</div>
					</div>
				</div>
			</div>
			<div v-else class="space-y-2 w-56">
				<Combobox v-model="selectedContact">
					<ComboboxInput 
						class="rounded-md w-full border-none focus:ring-0 py-2 pl-3 pr-10 text-sm leading-5 text-gray-900 bg-slate-100"
						autocomplete="off"
						@change="query = $event.target.value" 
					/>
					<ComboboxOptions
						class="w-56 absolute py-1 mt-1 overflow-auto text-base bg-white rounded-md shadow-lg max-h-60 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
					>
						<div
							v-if="filterdContacts.length === 0 && query !== ''"
							class="select-none relative py-2 px-4 text-gray-700 cursor-pointer"
							@click="createNewContact()"
						>
							Create new
						</div>
						<ComboboxOption
							v-slot="{ selected, active }"
							v-for="contactItem in filterdContacts" :key="contactItem"
							:value="contactItem"
						>
							<li
								class="cursor-default select-none relative py-2 pl-4 pr-4 text-gray-900"
								:class="{'bg-slate-50': active}"
							>
								<span
									class="block truncate"
									:class="{ 'font-medium': selected, 'font-normal': !selected }"
									>
									{{ contactItem }}
								</span>
							</li>
						</ComboboxOption>
					</ComboboxOptions>
				</Combobox>
				<div class="flex space-x-2">
					<div class="grow"></div>
					<Button appearance="primary" @click="updateContact()">Save</Button>
				</div>
			</div>
		</div>
		<div v-if="false">
			<div class="py-4 border-b space-y-3" v-if="otherTicketsOfContact && !editing">
				<div class="text-lg font-medium">{{ `Open Tickets (${otherTicketsOfContact.length})` }}</div>
				<div class="space-y-1 " v-for="ticket in otherTicketsOfContact" :key="ticket.name">
					<router-link :to="`/tickets/${ticket.name}`" class="text-slate-500 text-base">
						<div class="flex">
							<FeatherIcon name="link" class="w-4 h-4"/>
							<span class="text-slate-500 ml-2">{{ ticket.subject }}</span>
						</div>
					</router-link>
				</div>
			</div>
			<div class="py-4">
				<div class="text-lg font-medium">Activity</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, Input } from 'frappe-ui'
import {
	Combobox,
	ComboboxInput,
	ComboboxOptions,
	ComboboxOption,
} from '@headlessui/vue'

export default {
	name: "InfoPanel",
	props: ["ticket", "contact"],
	components: {
		FeatherIcon,
		Input,
		Combobox,
		ComboboxInput,
		ComboboxOption,
		ComboboxOptions
	},
	data() {
		return {
			editing: false,
			contactName: '',
			selectedContact:  '',
			query: ''
		}
	},
	resources: {
		otherTicketsOfContact() {
			return {
				method: 'helpdesk.api.ticket.get_other_tickets_of_contact',
				params: {
					ticket_id: this.ticket.name,
				},
				auto: true
			}
		},
	},
	computed: {
		contactFullName() {
			if (this.contact) {
				return (this.contact.first_name || "") + " " + (this.contact.last_name || "")
			}
		},
		otherTicketsOfContact() {
			return this.$resources.otherTicketsOfContact.data || null;
		},
		filterdContacts() {
			return this.query === ''
				? this.$tickets().get('contacts')
				: this.$tickets().get('contacts').filter((contactItem) => {
					return contactItem.toLowerCase().includes(this.query.toLowerCase())
				})
		}
	},
	methods: {
		updateContact() {
			this.editing = false
			console.log(`contact: ${this.selectedContact}`)
			this.$tickets(this.ticket.name).updateContact(this.selectedContact)
		},
		createNewContact() {

		}
	}
}
</script>

<style>

</style>