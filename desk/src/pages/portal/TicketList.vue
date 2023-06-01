<template>
	<div
		class="flex justify-between px-9 py-4 text-base text-gray-700 transition"
	>
		<div class="flex gap-4">
			<Dropdown :options="dropdownOptions">
				<template #default="{ open }">
					<div
						class="flex cursor-pointer select-none items-center gap-1 hover:text-gray-900"
					>
						{{ dropdownTitle }}
						<IconCaretDown v-if="!open" class="h-3 w-3" />
						<IconCaretUp v-if="open" class="h-3 w-3" />
					</div>
				</template>
			</Dropdown>
			<RouterLink
				:to="{ name: CUSTOMER_PORTAL_NEW_TICKET }"
				class="flex cursor-pointer select-none items-center gap-1 hover:text-gray-900"
			>
				New ticket
				<IconPlus class="h-3 w-3" />
			</RouterLink>
		</div>
		<div
			v-if="tickets.hasPreviousPage || tickets.hasNextPage"
			class="flex gap-2 text-xs"
		>
			<div
				v-if="tickets.hasPreviousPage"
				class="cursor-pointer"
				@click="tickets.previous()"
			>
				&leftarrow;
				{{ tickets.currentPage - 1 }}
			</div>
			<div class="font-medium text-gray-900">
				{{ tickets.currentPage }}
			</div>
			<div
				v-if="tickets.hasNextPage"
				class="cursor-pointer"
				@click="tickets.next()"
			>
				{{ tickets.currentPage + 1 }}
				&rightarrow;
			</div>
		</div>
	</div>
	<HelpdeskTable
		:columns="columns"
		:data="tickets.list?.data || []"
		row-key="name"
		:emit-row-click="true"
		:hide-checkbox="true"
		:hide-column-selector="true"
		@row-click="(ticketId) => handleRowClick(ticketId)"
	>
		<template #subject="{ data }">
			<div
				class="flex items-center gap-2"
				:class="{
					'font-medium': isHighlight(data),
					'text-gray-900': isHighlight(data),
				}"
			>
				<div class="line-clamp-1 max-w-lg">
					{{ data.subject }}
				</div>
				<div class="flex items-center gap-1 text-xs">
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
</template>

<script setup lang="ts">
import { onBeforeMount, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Dropdown } from "frappe-ui";
import dayjs from "dayjs";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { createListManager } from "@/composables/listManager";
import { CUSTOMER_PORTAL_TICKET, CUSTOMER_PORTAL_NEW_TICKET } from "@/router";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import IconCaretDown from "~icons/ph/caret-down";
import IconCaretUp from "~icons/ph/caret-up";
import IconHash from "~icons/espresso/hash";
import IconPlus from "~icons/ph/plus";

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
		colClass: "w-24",
	},
];

const tickets = createListManager({
	doctype: "HD Ticket",
	pageLength: 12,
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
		label: "Active tickets",
		handler() {
			filter("Active tickets", { status: ["in", ACTIVE_TICKET_TYPES] });
		},
	},
	{
		label: "Inative tickets",
		handler() {
			filter("Inactive tickets", { status: ["not in", ACTIVE_TICKET_TYPES] });
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
			return "Feedback needed";
		default:
			return status;
	}
}

function isHighlight(ticket) {
	return ticket.status === "Replied";
}

onBeforeMount(() => configStore.setTitle("My Tickets"));
onUnmounted(() => configStore.setTitle());
</script>
