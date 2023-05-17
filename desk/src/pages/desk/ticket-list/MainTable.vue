<template>
	<div class="overflow-x-scroll">
		<div class="flex w-max min-w-full flex-col">
			<div
				class="sticky top-0 z-50 flex items-center gap-2 border-y border-gray-200 bg-white px-9 py-1.5 text-sm text-gray-600"
			>
				<Input
					type="checkbox"
					input-class="cursor-pointer"
					class="mr-1"
					:value="allSelected"
					:onchange="(e) => toggleAllSelected(e.target.checked)"
				/>
				<div class="w-20">Type</div>
				<div ref="subjectCol" class="col-subject grow">Subject</div>
				<div class="w-40">Assignee</div>
				<div class="w-24">Status</div>
				<div class="w-24">Priority</div>
				<div v-if="columns['Due in']" class="w-24">Due in</div>
				<div v-if="columns['Created on']" class="w-36">Created on</div>
				<div v-if="columns['Last modified']" class="w-36">Last modified</div>
				<div v-if="columns['Source']" class="w-20">Source</div>
				<ColumnSelector class="ml-auto" />
			</div>
			<div class="divide-y px-6 py-2 text-base">
				<div
					v-for="t in tickets.list.data"
					:key="t.name"
					class="flex h-11 w-full items-center gap-2 px-3 py-2 transition-all"
					:class="{
						'bg-gray-200': selected.has(t.name),
						'hover:bg-gray-300': selected.has(t.name),
						'hover:bg-gray-100': !selected.has(t.name),
					}"
				>
					<Input
						type="checkbox"
						class="mr-1 cursor-pointer"
						:value="selected.has(t.name)"
						@click="() => toggleOne(t.name)"
					/>
					<div class="line-clamp-1 w-20 text-gray-700">
						{{ t.ticket_type || "--" }}
					</div>
					<TicketSummary class="col-subject grow" :ticket-name="t.name" />
					<div class="w-40">
						<AssignedInfo :ticket-id="t.name" />
					</div>
					<div class="w-24">
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
					<div class="w-24">
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
						v-if="columns['Due in']"
						class="line-clamp-1 w-24 text-gray-700"
						:class="{
							'text-red-700': Date.parse(t.resolution_by) < Date.now(),
						}"
					>
						{{ t.resolution_by ? dayjs(t.resolution_by).fromNow() : "--" }}
					</div>
					<div
						v-if="columns['Created on']"
						class="line-clamp-1 w-36 text-gray-700"
					>
						{{ dayjs(t.creation).format(dateFormat) }}
					</div>
					<div
						v-if="columns['Last modified']"
						class="line-clamp-1 w-36 text-gray-700"
					>
						{{ dayjs(t.modified).format(dateFormat) }}
					</div>
					<div v-if="columns['Source']" class="line-clamp-1 w-20 text-gray-700">
						{{ t.via_customer_portal ? "Customer Portal" : "EMail" }}
					</div>
					<Dropdown
						:options="[
							{
								label: 'Copy link',
								handler() {
									copyTicketLink(t.name);
								},
							},
						]"
					>
						<template #default>
							<IconDotHorizontal class="h-4 w-4 cursor-pointer text-gray-700" />
						</template>
					</Dropdown>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useClipboard } from "@vueuse/core";
import { Dropdown } from "frappe-ui";
import dayjs from "dayjs";
import { AGENT_PORTAL_TICKET } from "@/router";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { createToast } from "@/utils/toasts";
import { useData } from "./data";
import AssignedInfo from "./AssignedInfo.vue";
import TicketSummary from "./TicketSummary.vue";
import ColumnSelector from "./ColumnSelector.vue";
import IconCaretDown from "~icons/ph/caret-down";
import IconCaretUp from "~icons/ph/caret-up";
import IconDotHorizontal from "~icons/espresso/dot-horizontal";

const router = useRouter();
const { copy } = useClipboard();
const ticketPriorityStore = useTicketPriorityStore();
const ticketStatusStore = useTicketStatusStore();
const { selected, tickets, toggleOne, selectAll, deselectAll, columns } =
	useData();

const dateFormat = "D/M/YYYY h:mm A";
const allSelected = computed(() => {
	return tickets.list?.data?.length === selected.value.size;
});

function toggleAllSelected(checked: boolean) {
	if (checked) selectAll();
	else deselectAll();
}

function statusDropdownOptions(ticketId: number, currentStatus: string) {
	return ticketStatusStore.options
		.filter((o) => o !== currentStatus)
		.map((o) => ({
			label: o,
			handler: () =>
				this.ticketList.setValue.submit({
					name: ticketId,
					status: o,
				}),
		}));
}

function priorityDropdownOptions(ticketId: number, currentPriority: string) {
	return ticketPriorityStore.names
		.filter((o) => o !== currentPriority)
		.map((o) => ({
			label: o,
			handler: () =>
				this.ticketList.setValue.submit({
					name: ticketId,
					priority: o,
				}),
		}));
}

async function copyTicketLink(name: number) {
	const loc = router.resolve({
		name: AGENT_PORTAL_TICKET,
		params: {
			ticketId: name,
		},
	});

	const base = window.location.protocol + "//" + window.location.host;
	const full = base + loc.href;

	await copy(full);

	createToast({
		title: "Link copied to clipboard",
		icon: "check",
		iconClasses: "text-green-600",
	});
}
</script>

<style scoped>
.col-subject {
	min-width: 420px;
	max-width: 600px;
}
</style>
