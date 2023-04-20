<template>
	<div class="flex">
		<TabGroup vertical>
			<div class="main-panel">
				<TabPanels>
					<TabPanel v-for="item in items" :key="item.name">
						<component :is="item.component" />
					</TabPanel>
				</TabPanels>
			</div>
			<TabList class="sidebar flex flex-col gap-2 border-l">
				<Tab v-for="item in items" :key="item.name" v-slot="{ selected }">
					<div
						class="flex h-7 w-7 items-center justify-center rounded-lg"
						:class="{
							'bg-gray-200': selected,
							'text-gray-900': selected,
							'text-gray-600': !selected,
						}"
					>
						<component :is="item.icon" />
					</div>
				</Tab>
			</TabList>
		</TabGroup>
	</div>
</template>

<script setup lang="ts">
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from "@headlessui/vue";
import ContactDetails from "./ContactDetails.vue";
import TicketDetails from "./TicketDetails.vue";
import TicketHistory from "./TicketHistory.vue";
import IconActivity from "~icons/espresso/activity";
import IconAlert from "~icons/espresso/alert-circle";
import IconDetails from "~icons/espresso/details";

const items = [
	{
		name: "Ticket Details",
		component: TicketDetails,
		icon: IconDetails,
	},
	{
		name: "Contact Details",
		component: ContactDetails,
		icon: IconAlert,
	},
	{
		name: "Ticket History",
		component: TicketHistory,
		icon: IconActivity,
	},
];
</script>

<style scoped>
.main-panel {
	width: 310px;
}

.sidebar {
	width: 50px;
	padding: 16px 12px 0 10px;
}

.icon {
	height: 18px;
	width: 18px;
}
</style>
