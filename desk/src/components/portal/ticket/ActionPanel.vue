<template>
	<div class="px-3" v-if="ticket">
		<div class="py-4 space-y-3">
			<div class="text-base space-y-2">
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Status</div>
					<CustomDropdown
						v-if="ticketStatuses"
						:options="statusesAsDropdownOptions()"
						class="text-base w-56"
					>
						<template
							v-slot="{ toggleAssignees }"
							@click="toggleAssignees"
							class="w-full"
						>
							<div class="w-full">
								<div
									class="flex w-56 py-1 hover:bg-slate-50 space-x-1"
								>
									<div
										v-if="ticket.status"
										class="grow w-52 text-left"
									>
										{{ ticket.status }}
									</div>
									<div
										v-else
										class="text-base grow w-52 text-left text-gray-400"
									>
										set status
									</div>
									<CustomIcons
										name="select"
										class="w-4 h-4 float-right"
									/>
								</div>
							</div>
						</template>
					</CustomDropdown>
				</div>
			</div>
		</div>
		<Dialog
			:options="{ title: 'Create New Type' }"
			v-model="openCreateNewTicketTypeDialog"
		>
			<template #body-content>
				<div class="space-y-4">
					<Input
						type="text"
						v-model="newType"
						placeholder="eg: Bug"
					/>
					<div class="flex float-right space-x-2">
						<Button @click="createAndAssignTicketTypeFromDialog()"
							>Create and Assign</Button
						>
						<Button
							@click="createTicketFromDialog()"
							appearance="primary"
							>Create</Button
						>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown, Input, Dialog } from "frappe-ui"
import CustomDropdown from "@/components/desk/global/CustomDropdown.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { inject } from "@vue/runtime-core"

export default {
	name: "ActionPanel",
	props: ["ticketId"],
	components: {
		FeatherIcon,
		Dropdown,
		CustomDropdown,
		Input,
		Dialog,
		CustomIcons,
	},
	data() {
		return {
			openCreateNewTicketTypeDialog: false,
			newType: "",
		}
	},
	setup() {
		const user = inject("user")
		const tickets = inject("tickets")
		const ticketStatuses = inject("ticketStatuses")
		const ticketController = inject("ticketController")

		return {
			user,
			tickets,
			ticketStatuses,
			ticketController,
		}
	},
	computed: {
		ticket() {
			return this.tickets[this.ticketId] || null
		},
	},
	methods: {
		statusesAsDropdownOptions() {
			let statusItems = []
			;["Open", "Close"].forEach((status) => {
				statusItems.push({
					label: status,
					handler: () => {
						this.ticketController.set(
							this.ticketId,
							"status",
							status == "Open" ? "Open" : "Closed"
						)
					},
				})
			})
			return statusItems
		},
	},
}
</script>

<style></style>
