<template>
	<span>
		<div class="space-y-3 px-9 pb-4 pt-6">
			<div class="flex items-center justify-between">
				<div class="text-2xl font-semibold text-gray-900">My Tickets</div>
				<div class="flex gap-2">
					<div
						class="flex items-center justify-between text-base text-gray-700 transition"
					>
						<div class="flex gap-4">
							<Dropdown :options="dropdownOptions">
								<template #default="{ open }">
									<Button
										:label="dropdownTitle"
										:icon-right="open ? 'chevron-up' : 'chevron-down'"
									/>
								</template>
							</Dropdown>
						</div>
					</div>
					<RouterLink :to="{ name: CUSTOMER_PORTAL_NEW_TICKET }">
						<Button
							class="bg-gray-900 text-white hover:bg-gray-800"
							label="New ticket"
							icon-right="plus"
						/>
					</RouterLink>
				</div>
			</div>
		</div>
		<span v-if="!isEmpty(tickets.list?.data)">
			<HelpdeskTable
				:columns="columns"
				:data="tickets.list?.data"
				row-key="name"
				:emit-row-click="true"
				:hide-checkbox="true"
				:hide-column-selector="true"
				@row-click="(ticketId) => handleRowClick(ticketId)"
			>
				<template #subject="{ data }">
					<div
						class="flex items-center justify-between"
						:class="{
							'font-medium': isHighlight(data),
							'text-gray-900': isHighlight(data),
						}"
					>
						<div class="line-clamp-1 max-w-lg">
							{{ data.subject }}
						</div>
						<div class="mx-2 flex items-center gap-1 text-xs">
							<IconHash class="h-3 w-3" />
							{{ data.name }}
						</div>
					</div>
				</template>
				<template #status="{ data }">
					{{ transformStatus(data.status) }}
				</template>
				<template #creation="{ data }">
					{{ dayjs(data.creation).fromNow() }}
				</template>
			</HelpdeskTable>
			<ListNavigation v-bind="tickets" class="px-9 py-3" />
		</span>
		<div
			v-else
			class="flex h-64 items-center justify-center text-base text-gray-900"
		>
			📭 No tickets
		</div>
	</span>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Dropdown } from "frappe-ui";
import dayjs from "dayjs";
import { isEmpty } from "lodash";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { createListManager } from "@/composables/listManager";
import { CUSTOMER_PORTAL_TICKET, CUSTOMER_PORTAL_NEW_TICKET } from "@/router";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import IconCaretDown from "~icons/ph/caret-down";
import IconCaretUp from "~icons/ph/caret-up";
import IconHash from "~icons/espresso/hash";

const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();
const columns = [
	{
		title: "Subject",
		colKey: "subject",
		colClass: "grow",
	},
	{
		title: "Status",
		colKey: "status",
		colClass: "w-32",
	},
	{
		title: "Created",
		colKey: "creation",
		colClass: "w-32",
	},
];

const tickets = createListManager({
	doctype: "HD Ticket",
	pageLength: 10,
	fields: ["name", "creation", "subject", "status"],
	filters: {
		raised_by: ["=", authStore.userId],
	},
	auto: true,
});

const ACTIVE_TICKET_TYPES = ["Open", "Replied"];
const dropdownTitle = ref("All tickets");
const dropdownOptions = [
	{
		label: "All tickets",
		handler() {
			filter("All tickets", { status: undefined });
		},
	},
	{
		label: "Open tickets",
		handler() {
			filter("Open tickets", { status: ["in", ACTIVE_TICKET_TYPES] });
		},
	},
	{
		label: "Closed tickets",
		handler() {
			filter("Closed tickets", { status: ["not in", ACTIVE_TICKET_TYPES] });
		},
	},
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function filter(title: string, filters: Record<string, any>) {
	tickets.update({
		...tickets,
		filters: {
			...tickets.filters,
			...filters,
		},
	});
	tickets.reload();
	dropdownTitle.value = title;
}

function handleRowClick(ticketId: number) {
	router.push({ name: CUSTOMER_PORTAL_TICKET, params: { ticketId } });
}

function transformStatus(status: string) {
	switch (status) {
		case "Replied":
			return "Awaiting reply";
		default:
			return status;
	}
}

function isHighlight(ticket) {
	return ticket.status === "Replied";
}

onMounted(() => configStore.setTitle("My Tickets"));
onUnmounted(() => configStore.setTitle());
</script>
