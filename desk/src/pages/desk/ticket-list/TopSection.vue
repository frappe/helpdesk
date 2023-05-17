<template>
	<div class="flex justify-between px-6 py-3">
		<div class="flex gap-2">
			<PresetFilters doctype="HD Ticket" />
			<Dropdown
				:options="byStatus"
				:button="{
					label: 'Status',
					iconRight: 'chevron-down',
				}"
			/>
			<Dropdown
				:options="byPriority"
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
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useRoute } from "vue-router";
import { createResource, Dropdown } from "frappe-ui";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useListFilters } from "@/composables/listFilters";
import CompositeFilters from "./CompositeFilters.vue";
import PresetFilters from "./PresetFilters.vue";
import IconSort from "~icons/espresso/sort-arrow";

const router = useRouter();
const route = useRoute();
const ticketPriorityStore = useTicketPriorityStore();
const ticketStatusStore = useTicketStatusStore();
const listFilters = useListFilters();

const sortOptionsRes = createResource({
	url: "helpdesk.extends.doc.sort_options",
	auto: true,
	params: {
		doctype: "HD Ticket",
	},
});

const sortOptions = computed(() => {
	return sortOptionsRes.data?.map((o) => ({
		label: o,
		handler: () =>
			router.push({
				query: {
					...route.query,
					sort: encodeURIComponent(o.replaceAll(" ", "-")),
				},
			}),
	}));
});

const byStatus = ticketStatusStore.options.map((status) => ({
	label: status,
	handler: () => filterByField("status", status),
}));

const byPriority = ticketPriorityStore.names.map((priority) => ({
	label: priority,
	handler: () => filterByField("priority", priority),
}));

function filterByField(fieldname: string, value: string) {
	const f = [
		{
			fieldname,
			filter_type: "is",
			value,
		},
	];

	listFilters.applyQuery(f);
}
</script>
