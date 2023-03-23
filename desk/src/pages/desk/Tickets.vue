<template>
	<div class="flex flex-col text-gray-700">
		<div class="px-6 py-4 text-2xl font-semibold text-gray-900">Tickets</div>
		<div class="flex justify-between px-6 py-3">
			<div class="flex gap-2">
				<PresetFilters doctype="Ticket" />
				<Dropdown
					:options="filterByStatusOptions"
					:button="{
						label: 'Status',
						iconRight: 'chevron-down',
						class: 'text-gray-500 bg-gray-200 rounded-lg',
					}"
				/>
				<Dropdown
					:options="filterByPriorityOptions"
					:button="{
						label: 'Priority',
						iconRight: 'chevron-down',
						class: 'text-gray-500 bg-gray-200 rounded-lg',
					}"
				/>
			</div>
			<div class="flex items-center gap-1">
				<FilterBox doctype="Ticket" />
				<Dropdown
					:options="sortDropdownOptions"
					:button="{
						label: 'Sort',
						iconLeft: 'list',
						class: 'text-gray-500 bg-gray-200 rounded-lg',
					}"
				/>
			</div>
		</div>
		<div class="px-6 font-sans text-base text-gray-500">
			<div class="flex items-center border-y border-gray-300 p-2">
				<div class="pl-1 pr-4">
					<Input
						type="checkbox"
						input-class="cursor-pointer"
						:value="allSelected"
						:onchange="(e) => toggleAllSelected(e.target.checked)"
					/>
				</div>
				<div class="basis-1/3">Summary</div>
				<div class="flex basis-2/3">
					<div class="basis-1/4">Assigned To</div>
					<div class="basis-1/4">Type</div>
					<div class="basis-1/4">Status</div>
					<div class="basis-1/4">Priority</div>
				</div>
			</div>
		</div>
		<div class="overflow-x-scroll px-6 py-2 font-sans text-base">
			<div
				v-for="t in __l.list.data"
				:key="t.name"
				class="flex w-full cursor-pointer items-center rounded-lg border-b p-2 shadow-black transition-all last-of-type:border-none hover:shadow-[0px_0px_20px_5px_#e2e8f0]"
			>
				<div class="pl-1 pr-4">
					<Input
						type="checkbox"
						input-class="cursor-pointer"
						:value="selected.has(t.name)"
						:onchange="(e) => toggleOne(t.name, e.target.checked)"
					/>
				</div>
				<div class="basis-1/3">
					<TicketSummary :ticket-name="t.name" />
				</div>
				<div class="flex basis-2/3 items-center">
					<div class="basis-1/4">
						<AssignedInfo :ticket-id="t.name" />
					</div>
					<div class="basis-1/4">
						{{ t.ticket_type }}
					</div>
					<div class="basis-1/4">
						<Dropdown
							:options="statusDropdownOptions(t.name, t.status)"
							:button="{
								label: t.status,
								iconRight: 'chevron-down',
								class: 'bg-white text-gray-500 hover:bg-white',
							}"
						/>
					</div>
					<div class="basis-1/4">
						<Badge :color-map="priorityColorMap" :label="t.priority" />
					</div>
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
				<Button
					v-show="__l.hasPreviousPage"
					icon="chevron-left"
					class="h-5 w-5 rounded-full bg-gray-200"
					@click="__l.previous"
				/>
				<Button
					v-show="__l.hasNextPage"
					icon="chevron-right"
					class="h-5 w-5 rounded-full bg-gray-200"
					@click="__l.next"
				/>
			</div>
		</div>
		<div
			v-show="selected.size"
			class="fixed inset-x-0 bottom-8 mx-auto w-max font-sans text-base"
		>
			<div
				class="flex items-center rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-[0px_0px_20px_5px_#e2e8f0]"
			>
				<div class="w-64">
					<div class="inline-block align-middle">
						<Input type="checkbox" :value="true" :disabled="true" />
					</div>
					<div class="inline-block pl-2 align-middle">
						{{ selected.size }}
						tickets selected
					</div>
				</div>
				<div>
					<Dropdown
						:options="agentsAsDropdownOptions"
						:button="{
							label: 'Assign',
							iconLeft: 'plus-circle',
							class: 'bg-white text-gray-500',
						}"
					/>
				</div>
				<div class="text-gray-300">&#x007C;</div>
				<div>
					<Button
						label="Select all"
						class="bg-white text-gray-500"
						:disabled="allSelected"
						@click="selectAll"
					/>
				</div>
				<div>
					<Button
						icon="x"
						class="bg-white text-gray-500"
						@click="deselectAll"
					/>
				</div>
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
import { Dropdown } from "frappe-ui";
import TicketSummary from "@/components/desk/tickets/TicketSummary.vue";
import PresetFilters from "@/components/desk/tickets/PresetFilters.vue";
import FilterBox from "@/components/desk/tickets/FilterBox.vue";
import AssignedInfo from "@/components/desk/tickets/AssignedInfo.vue";
import { createListManager } from "@/composables/listManager";
import { useListFilters } from "@/composables/listFilters";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketPriorityStore } from "@/stores/ticketPriority";

export default {
	name: "Tickets",
	components: {
		AssignedInfo,
		Dropdown,
		FilterBox,
		PresetFilters,
		TicketSummary,
	},
	inject: ["agents", "user"],
	setup() {
		const listStart = ref(0);
		const listEnd = ref(0);
		const selected = ref(new Set());
		const listFilters = useListFilters();
		const ticketStatusStore = useTicketStatusStore();
		const ticketPriorityStore = useTicketPriorityStore();

		const __l = createListManager({
			doctype: "Ticket",
			pageLength: 15,
		});

		return {
			listStart,
			listEnd,
			selected,
			listFilters,
			ticketStatusStore,
			ticketPriorityStore,
			__l,
		};
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
	computed: {
		allSelected() {
			if (this.$_.isEmpty(this.__l.list.data)) return;
			return this.__l.list.data.length === this.selected.size;
		},
		filterByPriorityOptions() {
			return this.ticketPriorityStore.getNames().map((priority) => ({
				label: priority,
				handler: () => this.filterByPriority(priority),
			}));
		},
		filterByStatusOptions() {
			return this.ticketStatusStore.options.map((status) => ({
				label: status,
				handler: () => this.filterByStatus(status),
			}));
		},
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach((agent) => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$resources.bulkAssignTicketToAgent.submit({
								ticket_ids: Array.from(this.selected),
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
										ticket_ids: Array.from(this.selected),
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
	mounted() {
		this.listStart = this.__l.start + 1;
		this.listEnd = this.__l.start + this.__l.pageLength;
	},
	methods: {
		toggleOne(ticketId, checked) {
			if (checked) this.selected.add(ticketId);
			else this.selected.delete(ticketId);
		},
		selectAll() {
			this.__l.list.data.forEach((t) => this.selected.add(t.name));
		},
		deselectAll() {
			this.selected.clear();
		},
		toggleAllSelected(checked) {
			if (checked) this.selectAll();
			else this.deselectAll();
		},
		setTicketStatus(ticketId, status) {
			this.__l.setValue.submit({
				name: ticketId,
				status,
			});
		},
		statusDropdownOptions(ticketId, currentStatus) {
			return this.ticketStatusStore.options
				.filter((o) => o !== currentStatus)
				.map((o) => ({
					label: o,
					handler: () => this.setTicketStatus(ticketId, o),
				}));
		},
		filterByPriority(priority) {
			this.filterByField("priority", priority);
		},
		filterByStatus(status) {
			this.filterByField("status", status);
		},
		filterByField(fieldname, value) {
			const f = [
				{
					fieldname,
					filter_type: "is",
					value,
				},
			];
			this.listFilters.applyQuery(this.listFilters.toQuery(f));
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
					this.$toast({
						title: "Tickets assigned to agent",
						icon: "check",
						iconClasses: "text-green-500",
					});
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
