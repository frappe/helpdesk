<template>
	<div class="flex flex-col text-gray-700">
		<div class="px-3 py-4 text-2xl font-semibold text-gray-900">Tickets</div>
		<div class="flex justify-between">
			<div>
				<PresetFilters doctype="Ticket" class="p-3" />
			</div>
			<div class="flex gap-1 items-center">
				<FilterBox doctype="Ticket" />
				<Dropdown
					:options="sortDropdownOptions"
					:button="{
						label: 'Sort',
						class: 'text-base',
					}"
					class="p-3"
				/>
			</div>
		</div>
		<div class="px-3 font-sans text-base text-gray-500">
			<div
				class="flex items-center justify-between border-y border-gray-300 p-2"
			>
				<div class="basis-1/3">Summary</div>
				<div>Assigned To</div>
				<div>Type</div>
				<div>Status</div>
				<div>Priority</div>
			</div>
		</div>
		<div class="overflow-x-scroll px-3 font-sans text-base">
			<div
				v-for="t in __l.list.data"
				:key="t.name"
				class="flex w-full items-center justify-between gap-2 border-b p-2 last-of-type:border-none"
			>
				<div class="basis-1/3">
					<TicketSummary :ticket-name="t.name" />
				</div>
				<div class="flex items-center gap-2">
					<AgentAvatar agent="hello@ssiyad.com" />
					Sabu Siyad
				</div>
				<div>
					{{ t.ticket_type }}
				</div>
				<div>
					{{ t.status }}
				</div>
				<div>
					<Badge :color-map="priorityColorMap" :label="t.priority" />
				</div>
			</div>
		</div>
		<div class="grow"></div>
		<div class="flex justify-between border-t p-4 font-sans text-base">
			<div class="text-gray-700">
				Showing {{ listStart }} to {{ listEnd }} of {{ __l.totalCount }}
			</div>
			<div class="flex items-center gap-2">
				Page
				<div
					class="flex h-5 w-5 flex-wrap content-center justify-center rounded-md bg-gray-200"
				>
					{{ __l.currentPage }}
				</div>
				of {{ __l.totalPages }}
				<Button v-show="__l.hasPreviousPage" icon="chevron-left" class="h-5 w-5 rounded-full bg-gray-200" @click="__l.previous" />
				<Button v-show="__l.hasNextPage" icon="chevron-right" class="h-5 w-5 rounded-full bg-gray-200" @click="__l.next" />
			</div>
		</div>
		<NewTicketDialog
			v-model="showNewTicketDialog"
			@close="showNewTicketDialog = false"
			@ticket-created="
				() => {
					showNewTicketDialog = false;
				}
			"
		/>
	</div>
</template>

<script>
import { ref } from "vue";
import { FeatherIcon, Dropdown, Tooltip } from "frappe-ui";
import AgentAvatar from "@/components/global/AgentAvatar.vue";
import TicketSummary from "@/components/desk/tickets/TicketSummary.vue";
import PresetFilters from "@/components/desk/tickets/PresetFilters.vue";
import FilterBox from "@/components/desk/tickets/FilterBox.vue";
import { createListManager } from "@/composables/listManager";

export default {
	name: "Tickets",
	components: {
		Dropdown,
		AgentAvatar,
		PresetFilters,
		TicketSummary,
		FilterBox,
	},
	inject: ["agents", "user"],
	setup() {
		const listStart = ref(0);
		const listEnd = ref(0);

		const __l = createListManager({
			doctype: "Ticket",
			pageLength: 5,
		});

		return {
			listStart,
			listEnd,
			__l,
		};
	},
	mounted() {
		this.listStart = this.__l.start + 1;
		this.listEnd = this.__l.start + this.__l.pageLength;
	},
	data() {
		function sortBy(key, dir) {
			this.$router.push({
				query: { q: this.$route.query.q, sortBy: key, sortDirection: dir },
			});
		}

		const sortOptions = [
			{ label: "Ticket Type", value: "ticket_type" },
			{ label: "Modified", value: "modified" },
			{ label: "Created", value: "created" },
		];

		const sortDropdownOptions = sortOptions.map((o) => ({
			label: o.label,
			handler: sortBy.bind(this, o.value, o.sortDirection || "desc"),
		}));

		return {
			priorityColorMap: {
				Urgent: "red",
				High: "yellow",
				Medium: "green",
				Low: "blue",
			},
			showNewTicketDialog: false,
			sortDropdownOptions,
		};
	},
	methods: {
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach((agent) => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$resources.bulkAssignTicketToAgent.submit({
								ticket_ids: Object.keys(
									this.$refs.ticketList.manager.selectedItems
								),
								agent_id: agent.name,
							});
						},
					});
				});
				let options = [];
				if (this.user.agent) {
					options.push({
						group: "Myself",
						hideLabel: true,
						items: [
							{
								label: "Assign to me",
								handler: () => {
									this.$resources.bulkAssignTicketToAgent.submit({
										ticket_ids: Object.keys(
											this.$refs.ticketList.manager.selectedItems
										),
										agent_id: this.user.agent.name,
									});
								},
							},
						],
					});
				}
				options.push({
					group: "All Agents",
					hideLabel: true,
					items: agentItems,
				});
				return options;
			} else {
				return null;
			}
		},
	},
	resources: {
		bulkAssignTicketStatus() {
			return {
				url: "frappedesk.api.ticket.bulk_assign_ticket_status",
				onSuccess: (res) => {
					//res: {docs: Ticket Docs, status: NewStatus}
					this.$refs.ticketList.manager.selectedItems = [];
					this.$refs.ticketList.manager.reload();

					this.$toast({
						title: `Tickets marked as ${res.status}.`,
						icon: "check",
						iconClasses: "text-green-500",
					});

					this.$event.emit("update_ticket_list");
				},
				onError: () => {
					this.$toast({
						title: "Unable to mark tickets as closed.",
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
			};
		},
		bulkAssignTicketToAgent() {
			return {
				url: "frappedesk.api.ticket.bulk_assign_ticket_to_agent",
				onSuccess: () => {
					this.$refs.ticketList.manager.selectedItems = [];
					this.$refs.ticketList.manager.reload();

					this.$toast({
						title: "Tickets assigned to agent",
						icon: "check",
						iconClasses: "text-green-500",
					});

					this.$event.emit("update_ticket_list");
				},
				onError: () => {
					this.$toast({
						title: "Unable to assign tickets to agent.",
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
			};
		},
	},
};
</script>
