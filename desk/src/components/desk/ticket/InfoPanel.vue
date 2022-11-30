<template>
	<div class="pt-[20px] h-full flex flex-col" v-if="ticket">
		<div
			class="shrink-0 text-base px-[16px] pb-[17px]"
			:class="editingContact ? '' : 'border-b'"
		>
			<LoadingText v-if="updatingContact" />
			<div v-else>
				<div v-if="!editingContact">
					<div v-if="contact" class="space-y-[12px]">
						<div class="flex flex-row items-center space-x-[12px]">
							<div class="w-7">
								<CustomAvatar
									:label="contactFullName"
									:imageURL="contact?.image"
									size="md"
								/>
							</div>
							<a
								:title="contactFullName"
								class="grow truncate font-normal text-base"
								>{{ contactFullName }}</a
							>
							<div class="flex">
								<FeatherIcon
									name="edit-2"
									class="stroke-slate-400 w-4 h-4 cursor-pointer"
									@click="
										() => {
											editingContact = !editingContact
										}
									"
								/>
							</div>
						</div>
						<div
							v-if="contact.phone_nos.length > 0"
							class="flex space-x-[12px] items-center"
						>
							<FeatherIcon
								name="phone"
								class="stroke-gray-500"
								style="width: 15px"
							/>
							<div
								class="flex flex-row space-x-[12px] items-center"
								v-for="phone_no in contact.phone_nos"
								:key="phone_no"
							>
								<a
									:title="phone_no.phone"
									class="text-gray-700 text-base"
									>{{ phone_no.phone }}</a
								>
								<div
									class="bg-blue-500 text-white px-2 py-0.5 rounded-md shadow-sm hover:shadow-md"
									role="button"
									@click="
										() => {
											$event.emit('dialer:make-call', {
												ticketId: ticket.name,
												to: phone_no.phone,
											})
										}
									"
								>
									Call
								</div>
							</div>
						</div>
						<div
							v-if="contact.email_ids.length > 0"
							class="flex space-x-[12px]"
						>
							<FeatherIcon
								name="mail"
								class="stroke-gray-500 mt-[2.5px]"
								style="width: 15px; height: 15px"
							/>
							<div
								class="space-y-1 max-w-[173px] break-words"
								v-for="email in contact.email_ids"
								:key="email"
							>
								<div
									:title="email.email_id"
									class="text-gray-700 text-base"
								>
									<a :title="email.email_id">{{
										email.email_id
									}}</a>
								</div>
							</div>
						</div>
					</div>
					<div v-else>
						<div
							v-if="!updatingContact"
							class="flex flex-row-reverse"
						>
							<FeatherIcon
								name="edit-2"
								class="stroke-slate-400 w-4 h-4 cursor-pointer"
								@click="
									() => {
										editingContact = !editingContact
									}
								"
							/>
						</div>
					</div>
				</div>
				<div v-else class="flex items-center space-x-2 mb-2 w-full">
					<div class="grow w-full">
						<!-- TODO: use the new functionalities of autocomplete -->
						<Autocomplete />
					</div>
					<FeatherIcon
						name="x"
						class="stroke-slate-400 w-4 h-4 cursor-pointer hover:stroke-red-500"
						@click="
							() => {
								editingContact = !editingContact
							}
						"
					/>
				</div>
			</div>
		</div>
		<div class="grow" v-if="!editingContact">
			<div class="h-full flex flex-col">
				<div
					class="shrink-0 border-b p-[16px] space-y-1 select-none"
					v-if="otherTicketsOfContact"
				>
					<div
						class="flex flex-row items-center"
						:class="
							otherTicketsOfContact.length > 0
								? 'cursor-pointer'
								: ''
						"
						@click="
							() => {
								showOtherTicketsOfContacts =
									!showOtherTicketsOfContacts
							}
						"
					>
						<div
							class="grow text-gray-600 text-[11px] font-semibold"
						>
							OPEN TICKETS ({{ otherTicketsOfContact.length }})
						</div>
						<FeatherIcon
							v-if="otherTicketsOfContact.length > 0"
							class="h-[15px] w-[15px] stroke-gray-500"
							:name="
								showOtherTicketsOfContacts
									? 'chevron-up'
									: 'chevron-down'
							"
						/>
					</div>
					<div
						v-if="
							showOtherTicketsOfContacts &&
							otherTicketsOfContact.length > 0
						"
						class="overflow-scroll pt-[4px] space-y-[4px] text-gray-700 font-normal"
					>
						<div
							v-for="(_ticket, index) in otherTicketsOfContact"
							:key="_ticket.name"
							:set="(maxCount = 5)"
						>
							<router-link
								v-if="index <= maxCount"
								:to="
									index < maxCount
										? `/frappedesk/tickets/${_ticket.name}`
										: `/frappedesk/tickets/?contact=${JSON.stringify(
												['is', contact.name]
										  )}`
								"
								class="text-[12px] rounded"
							>
								<div class="py-[1px]">
									<div
										v-if="index < maxCount"
										class="flex flex-row space-x-[12px] items-center hover:bg-gray-100"
									>
										<div class="w-[15px] h-[15px]">
											<FeatherIcon
												name="arrow-up-right"
												class="w-[15px] h-[15px] stroke-gray-500"
											/>
										</div>
										<div class="max-w-[180px]">
											<div class="truncate">
												<a
													class="text-[12px]"
													:title="_ticket.subject"
													>{{ _ticket.subject }}</a
												>
											</div>
										</div>
									</div>
									<div
										v-else
										class="hover:text-gray-600 flex flex-row-reverse text-[11px]"
									>
										View all
									</div>
								</div>
							</router-link>
						</div>
					</div>
				</div>
				<div class="h-full">
					<div
						class="flex flex-col p-[16px] select-none"
						:class="showTicketHistory ? '' : 'border-b'"
					>
						<div
							class="shrink-0 flex flex-row items-center cursor-pointer"
							@click="
								() => {
									showTicketHistory = !showTicketHistory
								}
							"
						>
							<div
								class="grow text-gray-600 text-[11px] font-semibold"
							>
								TICKET HISTORY
							</div>
							<FeatherIcon
								class="h-[15px] w-[15px] stroke-gray-500"
								:name="
									showTicketHistory
										? 'chevron-up'
										: 'chevron-down'
								"
							/>
						</div>
						<div
							v-if="showTicketHistory"
							class="overflow-y-scroll"
							:style="{
								height:
									viewportWidth > 768
										? `calc(100vh - ${getOffsetHeight}px)`
										: null,
							}"
						>
							<Activities :ticketId="ticket.name" />
						</div>
					</div>
				</div>
			</div>
		</div>
		<NewContactDialog
			v-model="showNewContactDialog"
			@contact-created="
				(contact) => {
					contactCreated(contact)
				}
			"
		/>
	</div>
</template>

<script>
import { FeatherIcon, Input, LoadingText } from "frappe-ui"
import CustomAvatar from "@/components/global/CustomAvatar.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import Activities from "@/components/desk/ticket/Activities.vue"
import Autocomplete from "@/components/global/Autocomplete.vue"
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue"
import { inject, ref, computed } from "vue"

export default {
	name: "InfoPanel",
	props: ["ticketId"],
	components: {
		FeatherIcon,
		Input,
		LoadingText,
		CustomAvatar,
		CustomIcons,
		Activities,
		Autocomplete,
		NewContactDialog,
	},
	setup(props, { context }) {
		const viewportWidth = inject("viewportWidth")

		const editingContact = ref(false)
		const updatingContact = ref(false)

		const showNewContactDialog = ref(false)

		const showOtherTicketsOfContacts = ref(false)
		const showTicketHistory = ref(false)

		const $tickets = inject("$tickets")
		const ticket = computed(() => {
			return $tickets.get({ ticketId: props.ticketId }, context).value
		})

		const $contacts = inject("$contacts")
		const contact = computed(() => {
			if (!(ticket.value && ticket.value.contact)) return null
			return $contacts.get({ contactId: ticket.value.contact }, context)
				.value
		})

		return {
			ticket,
			contact,

			viewportWidth,
			editingContact,
			updatingContact,
			showNewContactDialog,
			showTicketHistory,
			showOtherTicketsOfContacts,
		}
	},
	computed: {
		contactFullName() {
			if (this.contact) {
				return (
					(this.contact.first_name || "") +
					" " +
					(this.contact.last_name || "")
				).slice(0, 40)
			}
		},
		otherTicketsOfContact() {
			return this.$resources.otherTicketsOfContact.data || null
		},
		getOffsetHeight() {
			const offset = 290
			const multiplier = 30
			const maxCount = 5

			return (
				offset +
				multiplier *
					(this.showOtherTicketsOfContacts
						? this.otherTicketsOfContact.length <= maxCount
							? this.otherTicketsOfContact.length
							: maxCount
						: 0)
			)
		},
	},
	methods: {
		contactCreated(contact) {
			this.showNewContactDialog = false
			this.editingContact = false
			this.$tickets.set({
				ticketId: this.ticketId,
				fieldname: "contact",
				value: contact.name,
			})
			this.$tickets.set(this.ticketId, "contact", contact.name)
		},
	},
	resources: {
		otherTicketsOfContact() {
			return {
				cache: ["Other Tickets", "Action Panel", this.ticketId],
				method: "frappedesk.api.ticket.get_other_tickets_of_contact",
				params: {
					ticket_id: this.ticketId,
				},
				auto: true,
			}
		},
	},
}
</script>
