<template>
	<div class="flex flex-col text-gray-700">
		<div class="flex justify-between px-6 pt-6 pb-2 text-gray-900">
			<div class="text-2xl font-semibold">Tickets</div>
			<Button
				icon-left="plus"
				label="Add ticket"
				@click="showNewTicketDialog = true"
			/>
		</div>
		<div class="flex justify-between px-6 py-3">
			<div class="flex gap-2">
				<PresetFilters doctype="HD Ticket" />
				<Dropdown
					:options="filterByStatusOptions"
					:button="{
						label: 'Status',
						iconRight: 'chevron-down',
					}"
				/>
				<Dropdown
					:options="filterByPriorityOptions"
					:button="{
						label: 'Priority',
						iconRight: 'chevron-down',
					}"
				/>
			</div>
			<div class="flex items-center gap-2">
				<CompositeFilters />
				<Dropdown
					:options="sortOptions"
					:button="{
						label: 'Sort',
						iconLeft: 'list',
					}"
				>
					<template #default>
						<Button>
							<template #icon-left>
								<IconSort class="mr-1.5 h-4 w-4" />
							</template>
							<div>Sort</div>
						</Button>
					</template>
				</Dropdown>
			</div>
		</div>
		<div class="bg-gray-100 px-6 font-sans text-base text-gray-500">
			<div class="flex items-center gap-2 px-2 py-1.5">
				<div class="pl-1 pr-4">
					<Input
						type="checkbox"
						input-class="cursor-pointer"
						:value="allSelected"
						:onchange="(e) => toggleAllSelected(e.target.checked)"
					/>
				</div>
				<div class="w-1/3">Subject</div>
				<div class="flex w-2/3 gap-2">
					<div class="w-1/4">Assigned To</div>
					<div class="w-1/5">Type</div>
					<div class="w-1/6 pl-1">Status</div>
					<div class="w-1/6">Priority</div>
					<div class="w-1/5">Due In</div>
				</div>
			</div>
		</div>
		<div class="divide-y overflow-x-scroll px-6 py-2 font-sans text-base">
			<div
				v-for="t in ticketList.list.data"
				:key="t.name"
				class="flex w-full items-center gap-2 px-2 py-1 transition-all"
				:class="{
					'bg-gray-50': selected.has(t.name),
				}"
			>
				<div class="pl-1 pr-4">
					<Input
						type="checkbox"
						input-class="cursor-pointer"
						:value="selected.has(t.name)"
						:onchange="(e) => toggleOne(t.name, e.target.checked)"
					/>
				</div>
				<div class="w-1/3">
					<TicketSummary :ticket-name="t.name" />
				</div>
				<div class="flex w-2/3 items-center gap-2">
					<div class="w-1/4">
						<AssignedInfo :ticket-id="t.name" />
					</div>
					<div class="line-clamp-2 w-1/5">
						{{ t.ticket_type }}
					</div>
					<div class="w-1/6">
						<Dropdown
							:options="statusDropdownOptions(t.name, t.status)"
							:button="{
								label: t.status,
								iconRight: 'chevron-down',
								appearance: 'minimal',
								class: 'pl-1',
							}"
						/>
					</div>
					<div class="w-1/6">
						<Dropdown :options="priorityDropdownOptions(t.name, t.priority)">
							<template #default>
								<Badge
									:color-map="ticketPriorityStore.colorMap"
									:label="t.priority"
									class="cursor-pointer"
								/>
							</template>
						</Dropdown>
					</div>
					<div
						class="w-1/5 capitalize"
						:class="{
							'text-red-700': Date.parse(t.resolution_by) < Date.now(),
						}"
					>
						{{ t.resolution_by ? $dayjs(t.resolution_by).fromNow() : "" }}
					</div>
				</div>
			</div>
		</div>
		<div class="grow"></div>
		<div class="flex justify-between border-t p-3 font-sans text-base">
			<div class="text-gray-700">
				Showing {{ ticketList.startFrom }} to {{ ticketList.endAt }} of
				{{ ticketList.totalCount }}
			</div>
			<div class="flex items-center gap-2">
				Page
				<div
					class="flex h-5 w-5 flex-wrap content-center justify-center rounded-md bg-gray-200"
				>
					{{ ticketList.currentPage }}
				</div>
				of {{ ticketList.totalPages }}
				<Button
					v-show="ticketList.hasPreviousPage"
					icon="chevron-left"
					class="h-5 w-5 rounded-full bg-gray-200"
					@click="ticketList.previous"
				/>
				<Button
					v-show="ticketList.hasNextPage"
					icon="chevron-right"
					class="h-5 w-5 rounded-full bg-gray-200"
					@click="ticketList.next"
				/>
			</div>
		</div>
		<transition
			enter-active-class="duration-300 ease-out"
			enter-from-class="transform opacity-0"
			enter-to-class="opacity-100"
			leave-active-class="duration-200 ease-in"
			leave-from-class="opacity-100"
			leave-to-class="transform opacity-0"
		>
			<div
				v-show="selected.size"
				class="fixed inset-x-0 bottom-5 mx-auto w-max font-sans text-base"
			>
				<div
					class="bottom-bar flex items-center rounded-lg border border-gray-300 bg-white px-3 py-1"
				>
					<div class="w-64">
						<div class="inline-block align-middle">
							<Input type="checkbox" :value="true" :disabled="true" />
						</div>
						<div class="inline-block pl-2 align-middle">
							{{ ticketsSelectedText }}
						</div>
					</div>
					<div>
						<Dropdown
							:options="agentsAsDropdownOptions"
							:button="{
								label: 'Assign',
								iconLeft: 'plus-circle',
								appearance: 'minimal',
							}"
						/>
					</div>
					<div class="text-gray-300">&#x007C;</div>
					<div>
						<Button
							label="Select all"
							appearance="minimal"
							:disabled="allSelected"
							@click="selectAll"
						/>
					</div>
					<div>
						<Button icon="x" appearance="minimal" @click="deselectAll" />
					</div>
				</div>
			</div>
		</transition>
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
import { createListManager } from "@/composables/listManager";
import { useListFilters } from "@/composables/listFilters";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useAuthStore } from "@/stores/auth";
import NewTicketDialog from "@/components/desk/tickets/NewTicketDialog.vue";
import TicketSummary from "@/components/desk/tickets/TicketSummary.vue";
import PresetFilters from "@/components/desk/tickets/PresetFilters.vue";
import CompositeFilters from "@/components/desk/tickets/CompositeFilters.vue";
import AssignedInfo from "@/components/desk/tickets/AssignedInfo.vue";
import IconSort from "~icons/espresso/sort-arrow";

export default {
	name: "Tickets",
	components: {
		AssignedInfo,
		Dropdown,
		CompositeFilters,
		NewTicketDialog,
		PresetFilters,
		TicketSummary,
		IconSort,
	},
	inject: ["agents"],
	setup() {
		const authStore = useAuthStore();
		const listFilters = useListFilters();
		const selected = ref(new Set());
		const showNewTicketDialog = ref(false);
		const ticketPriorityStore = useTicketPriorityStore();
		const ticketStatusStore = useTicketStatusStore();

		const ticketList = createListManager({
			doctype: "HD Ticket",
			pageLength: 20,
		});

		return {
			authStore,
			listFilters,
			selected,
			showNewTicketDialog,
			ticketList,
			ticketPriorityStore,
			ticketStatusStore,
		};
	},
	computed: {
		sortOptions() {
			const options = this.$resources.sortOptions.data || [];
			return options.map((o) => ({
				label: o,
				value: o,
				handler: () =>
					this.$router.push({
						query: { ...this.$route.query, sort: encodeURIComponent(o) },
					}),
			}));
		},
		allSelected() {
			if (this.$_.isEmpty(this.ticketList.list.data)) return;
			return this.ticketList.list.data.length === this.selected.size;
		},
		ticketsSelectedText() {
			/** Number of selected items */
			const n = this.selected.size;

			/** Singular or Plural */
			const s = n > 1 ? "Tickets" : "Ticket";

			return `${n} ${s} selected`;
		},
		filterByPriorityOptions() {
			return this.ticketPriorityStore.names.map((priority) => ({
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
				if (this.authStore.isAgent) {
					options.push({
						group: "Myself",
						hideLabel: true,
						items: [
							{
								label: "Assign to me",
								handler: () => {
									this.$resources.bulkAssignTicketToAgent.submit({
										ticket_ids: Array.from(this.selected),
										agent_id: this.authStore.userId,
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
	methods: {
		toggleOne(ticketId, checked) {
			if (checked) this.selected.add(ticketId);
			else this.selected.delete(ticketId);
		},
		selectAll() {
			this.ticketList.list.data.forEach((t) => this.selected.add(t.name));
		},
		deselectAll() {
			this.selected.clear();
		},
		toggleAllSelected(checked) {
			if (checked) this.selectAll();
			else this.deselectAll();
		},
		statusDropdownOptions(ticketId, currentStatus) {
			return this.ticketStatusStore.options
				.filter((o) => o !== currentStatus)
				.map((o) => ({
					label: o,
					handler: () =>
						this.ticketList.setValue.submit({
							name: ticketId,
							status,
						}),
				}));
		},
		priorityDropdownOptions(ticketId, currentPriority) {
			return this.ticketPriorityStore.names
				.filter((o) => o !== currentPriority)
				.map((o) => ({
					label: o,
					handler: () =>
						this.ticketList.setValue.submit({
							name: ticketId,
							priority: o,
						}),
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
			this.listFilters.applyQuery(f);
		},
	},
	resources: {
		sortOptions() {
			return {
				url: "helpdesk.extends.doc.sort_options",
				auto: true,
				params: {
					doctype: "HD Ticket",
				},
			};
		},
		bulkAssignTicketStatus() {
			return {
				url: "helpdesk.api.ticket.bulk_assign_ticket_status",
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
				url: "helpdesk.api.ticket.bulk_assign_ticket_to_agent",
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

<style scoped>
.bottom-bar {
	box-shadow: 0px 0px 1px rgba(0, 0, 0, 0.3),
		0px 1px 3px 1px rgba(0, 0, 0, 0.05), 4px 4px 17px 6px rgba(0, 0, 0, 0.07);
}
</style>
