<template>
	<div class="h-screen w-screen bg-gray-100 p-8">
		<div
			class="mx-auto"
			:style="{
				width: '900px',
			}"
		>
			<div class="my-8 flex items-center justify-between text-base">
				<span>
					<img
						v-if="configStore.brandLogo"
						:src="configStore.brandLogo"
						class="h-8"
					/>
					<div v-else class="text-6xl text-gray-800">
						{{ configStore.helpdeskName }}
					</div>
				</span>
				<RouterLink :to="{ name: KNOWLEDGE_BASE_PUBLIC }">
					<div class="flex items-center gap-2">
						<IconKnowledgebase class="h-4 w-4" />
						Knowledge Base &rightarrow;
					</div>
				</RouterLink>
			</div>
			<div
				class="bg-white py-2"
				:style="{
					'box-shadow':
						'0px 0px 1px rgba(0, 0, 0, 0.45), 0px 1px 2px rgba(0, 0, 0, 0.1)',
				}"
			>
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
						<div
							class="flex cursor-pointer select-none items-center gap-1 hover:text-gray-900"
						>
							New Ticket
							<IconPlus class="h-3 w-3" />
						</div>
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
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { onBeforeMount, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Dropdown } from "frappe-ui";
import dayjs from "dayjs";
import { useConfigStore } from "@/stores/config";
import { createListManager } from "@/composables/listManager";
import { CUSTOMER_PORTAL_TICKET, KNOWLEDGE_BASE_PUBLIC } from "@/router";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import IconCaretDown from "~icons/ph/caret-down";
import IconCaretUp from "~icons/ph/caret-up";
import IconHash from "~icons/espresso/hash";
import IconKnowledgebase from "~icons/espresso/knowledge-base";
import IconPlus from "~icons/ph/plus";

const router = useRouter();
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
	auto: true,
	fields: ["name", "creation", "subject", "status"],
});

const ACTIVE_TICKET_TYPES = ["Open", "Replied"];
const dropdownTitle = ref("All Tickets");
const dropdownOptions = [
	{
		label: "All Tickets",
		handler() {
			filter("All Tickets", { status: undefined });
		},
	},
	{
		label: "Active Tickets",
		handler() {
			filter("Active Tickets", { status: ["in", ACTIVE_TICKET_TYPES] });
		},
	},
	{
		label: "Inative Tickets",
		handler() {
			filter("Inactive Tickets", { status: ["not in", ACTIVE_TICKET_TYPES] });
		},
	},
];

onBeforeMount(() => configStore.setTitle("My Tickets"));
onUnmounted(() => configStore.setTitle(""));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function filter(title: string, filters: Record<string, any>) {
	tickets.update({
		...tickets,
		filters,
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
</script>
