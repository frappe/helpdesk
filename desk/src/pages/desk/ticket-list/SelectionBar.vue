<template>
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
				class="selection-bar flex items-center gap-4 rounded-lg bg-white px-4 py-2"
			>
				<div class="w-64">
					<div class="inline-block align-middle">
						<Input type="checkbox" :value="true" :disabled="true" />
					</div>
					<div class="inline-block pl-2 align-middle text-gray-900">
						{{ ticketsSelectedText }}
					</div>
				</div>
				<Dropdown :options="assignOpts">
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
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createResource, Dropdown, FeatherIcon } from "frappe-ui";
import { useAgentStore } from "@/stores/agent";
import { createToast } from "@/utils/toasts";
import { useData } from "./data";

const agentStore = useAgentStore();
const { selected, selectAll, deselectAll } = useData();

const ticketsSelectedText = computed(() => {
	/** Number of selected items */
	const n = selected.value.size;

	/** Singular or Plural */
	const s = n > 1 ? "Tickets" : "Ticket";

	return `${n} ${s} selected`;
});

const bulkAssignTicketToAgent = createResource({
	url: "helpdesk.api.ticket.bulk_assign_ticket_to_agent",
	onSuccess: () => {
		createToast({
			title: "Tickets assigned to agent",
			icon: "check",
			iconClasses: "text-green-500",
		});
	},
	onError: () => {
		createToast({
			title: "Unable to assign tickets to agent.",
			icon: "x",
			iconClasses: "text-red-500",
		});
	},
});

const assignOpts = computed(() =>
	agentStore.options.map((a) => ({
		label: a.agent_name,
		handler: () =>
			bulkAssignTicketToAgent.submit({
				ticket_ids: Array.from(selected.value),
				agent_id: a.name,
			}),
	}))
);
</script>

<style scoped>
.selection-bar {
	box-shadow: 0px 0px 1px rgba(0, 0, 0, 0.3),
		0px 1px 3px 1px rgba(0, 0, 0, 0.05), 4px 4px 17px 6px rgba(0, 0, 0, 0.07);
}
</style>
