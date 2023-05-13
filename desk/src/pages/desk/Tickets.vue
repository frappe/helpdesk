<template>
	<div class="flex flex-col">
		<div class="flex justify-between px-6 pt-6 pb-2">
			<div class="text-2xl font-semibold text-gray-900">Tickets</div>
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
				<Dropdown :options="sortOptions">
					<template #default>
						<Button label="Sort">
							<template #icon-left>
								<IconSort class="mr-1.5 h-4 w-4" />
							</template>
						</Button>
					</template>
				</Dropdown>
			</div>
		</div>
		<div class="border-y border-gray-200 px-6 text-sm text-gray-600">
			<div class="flex items-center gap-2 px-2 py-1.5">
				<div class="pl-1 pr-4">
					<Input
						type="checkbox"
						input-class="cursor-pointer"
						:value="allSelected"
						:onchange="(e) => toggleAllSelected(e.target.checked)"
					/>
				</div>
				<div class="w-2/5">Subject</div>
				<div class="flex w-3/5 gap-2">
					<div class="w-1/4">Assigned To</div>
					<div class="w-1/5">Type</div>
					<div class="w-1/6">Status</div>
					<div class="w-1/6">Priority</div>
					<div class="w-1/5">Due In</div>
				</div>
			</div>
		</div>
		<div
			v-if="ticketList.totalCount"
			class="divide-y overflow-x-scroll px-6 py-2 text-base"
		>
			<div
				v-for="t in ticketList.list.data"
				:key="t.name"
				class="flex w-full items-center gap-2 px-2 py-1 transition-all"
				:class="{
					'bg-gray-100': selected.has(t.name),
				}"
			>
				<div class="cursor-pointer select-none pl-1 pr-4 text-gray-600">
					<IconTicket
						v-show="!selected.has(t.name)"
						class="h-4 w-4"
						@click="() => toggleOne(t.name, true)"
					/>
					<IconTicketSolid
						v-show="selected.has(t.name)"
						class="h-4 w-4"
						@click="() => toggleOne(t.name, false)"
					/>
				</div>
				<div class="w-2/5">
					<TicketSummary :ticket-name="t.name" />
				</div>
				<div class="flex w-3/5 items-center gap-2">
					<div class="w-1/4">
						<AssignedInfo :ticket-id="t.name" />
					</div>
					<div class="line-clamp-1 w-1/5 text-gray-700">
						{{ t.ticket_type }}
					</div>
					<div class="w-1/6">
						<Dropdown :options="statusDropdownOptions(t.name, t.status)">
							<template #default="{ open }">
								<div
									class="flex cursor-pointer select-none items-center gap-1 text-gray-700"
								>
									{{ t.status }}
									<IconCaretDown v-if="!open" class="h-3 w-3" />
									<IconCaretUp v-if="open" class="h-3 w-3" />
								</div>
							</template>
						</Dropdown>
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
						class="w-1/5 capitalize text-gray-700"
						:class="{
							'text-red-700': Date.parse(t.resolution_by) < Date.now(),
						}"
					>
						{{ t.resolution_by ? $dayjs(t.resolution_by).fromNow() : "" }}
					</div>
				</div>
			</div>
		</div>
		<div class="flex grow items-center justify-center text-sm text-gray-800">
			<div v-if="!ticketList.totalCount">
				🎉 Great news! There are currently no tickets to display. Keep up the
				good work!
			</div>
		</div>
		<div
			v-if="ticketList.totalCount"
			class="flex justify-between border-t p-3 text-base"
		>
			<div class="text-gray-600">
				Showing {{ ticketList.startFrom }} to {{ ticketList.endAt }} of
				{{ ticketList.totalCount }}
			</div>
			<div class="flex items-center gap-2 text-gray-600">
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
				class="fixed inset-x-0 bottom-5 mx-auto w-max text-base"
			>
				<div
					class="bottom-bar flex items-center gap-4 rounded-lg bg-white px-4 py-2"
				>
					<div class="w-64">
						<div class="inline-block align-middle">
							<Input type="checkbox" :value="true" :disabled="true" />
						</div>
						<div class="inline-block pl-2 align-middle text-gray-900">
							{{ ticketsSelectedText }}
						</div>
					</div>
					<Dropdown :options="agentsAsDropdownOptions">
						<template #default>
							<div class="flex cursor-pointer items-center gap-1 text-gray-700">
								<FeatherIcon name="plus-circle" class="h-4 w-4" />
								Assign
							</div>
						</template>
					</Dropdown>
					<div class="text-gray-300">&#x007C;</div>
					<div
						class="flex cursor-pointer items-center gap-1 text-gray-700"
						@click="selectAll"
					>
						Select all entries
					</div>
					<FeatherIcon
						name="x"
						class="h-4 w-4 cursor-pointer text-gray-600"
						@click="deselectAll"
					/>
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
import { Dropdown, FeatherIcon } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import { useListFilters } from "@/composables/listFilters";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { useKeymapStore } from "@/stores/keymap";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import NewTicketDialog from "@/components/desk/tickets/NewTicketDialog.vue";
import TicketSummary from "@/components/desk/tickets/TicketSummary.vue";
import PresetFilters from "@/components/desk/tickets/PresetFilters.vue";
import CompositeFilters from "@/components/desk/tickets/CompositeFilters.vue";
import AssignedInfo from "@/components/desk/tickets/AssignedInfo.vue";
import IconCaretDown from "~icons/ph/caret-down";
import IconCaretUp from "~icons/ph/caret-up";
import IconSort from "~icons/espresso/sort-arrow";
import IconTicket from "~icons/espresso/ticket";
import IconTicketSolid from "~icons/espresso/ticket-solid";

export default {
	name: "Tickets",
	components: {
		AssignedInfo,
		Dropdown,
		FeatherIcon,
		CompositeFilters,
		NewTicketDialog,
		PresetFilters,
		TicketSummary,
		IconCaretDown,
		IconCaretUp,
		IconSort,
		IconTicket,
		IconTicketSolid,
	},
	setup() {
		const agentStore = useAgentStore();
		const authStore = useAuthStore();
		const listFilters = useListFilters();
		const selected = ref(new Set());
		const showNewTicketDialog = ref(false);
		const ticketPriorityStore = useTicketPriorityStore();
		const ticketStatusStore = useTicketStatusStore();
		const keymapStore = useKeymapStore();

		const ticketList = createListManager({
			doctype: "HD Ticket",
			pageLength: 20,
		});

		return {
			agentStore,
			authStore,
			keymapStore,
			listFilters,
			selected,
			showNewTicketDialog,
			ticketList,
			ticketPriorityStore,
			ticketStatusStore,
		};
	},
	data() {
		return {
			shortcuts: [
				{
					button: "R",
					status: "Replied",
				},
				{
					button: "E",
					status: "Resolved",
				},
				{
					button: "C",
					status: "Closed",
				},
			],
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
			if (this.agentStore.options) {
				this.agentStore.options.forEach((agent) => {
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
	mounted() {
		this.shortcuts.forEach((o) => {
			this.keymapStore.add(
				["Control", o.button],
				() => {
					this.selected.forEach((ticketId) => {
						this.ticketList.setValue.submit({
							name: ticketId,
							status: o.status,
						});
					});
				},
				`Set ticket as ${o.status.toLowerCase()}`
			);
		});
	},
	beforeUnmount() {
		this.shortcuts.forEach((o) =>
			this.keymapStore.remove(["Control", o.button])
		);
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
							status: o,
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
