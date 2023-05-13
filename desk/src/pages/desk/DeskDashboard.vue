<template>
	<div class="flex flex-col">
		<div
			class="flex items-center px-6 pt-6 pb-2 text-2xl font-semibold text-gray-900"
		>
			Hello, {{ authStore.userFirstName }} 👋
		</div>
		<div
			v-if="isEmpty(items.data)"
			class="flex grow select-none items-center justify-center text-base text-gray-700"
		>
			📊 Oops, looks like there are no charts to display on the dashboard right
			now.
		</div>
		<div v-else class="grid grid-cols-3 gap-4 overflow-y-scroll p-4">
			<div
				v-for="i in items.data"
				:key="i.name"
				class="h-56 rounded-lg bg-gray-100 p-2"
			>
				<PieChart
					v-if="i.is_chart && i.chart_type === 'Pie'"
					:title="i.title"
					:data="i.data"
				/>
				<LineChart
					v-else-if="i.is_chart && i.chart_type === 'Line'"
					:title="i.title"
					:data="i.data"
				/>
				<SingleString v-else :title="i.title" :value="i.data" />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { isEmpty } from "lodash";
import LineChart from "@/components/charts/LineChart.vue";
import PieChart from "@/components/charts/PieChart.vue";
import SingleString from "@/components/charts/SingleString.vue";

const authStore = useAuthStore();
const items = createResource({
	url: "helpdesk.api.dashboard.get_many",
	auto: true,
});
</script>
