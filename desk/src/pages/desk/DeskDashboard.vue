<template>
	<div class="flex flex-col">
		<div class="flex items-center justify-between px-6 pt-6 pb-2">
			<div
				class="flex select-none items-center text-2xl font-semibold text-gray-900"
			>
				Hello,
				<div class="mx-1 text-gray-800">{{ authStore.userFirstName }}</div>
				👋
			</div>
			<Tooltip v-if="!isEmpty(items.data)" placement="left" :text="dateInfo">
				<IconInfo class="h-5 w-5 text-gray-800" />
			</Tooltip>
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
				:key="i.title"
				class="h-56 rounded-lg border bg-gray-50 p-2"
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
import { createResource, Tooltip } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { isEmpty } from "lodash";
import LineChart from "@/components/charts/LineChart.vue";
import PieChart from "@/components/charts/PieChart.vue";
import SingleString from "@/components/charts/SingleString.vue";
import IconInfo from "~icons/espresso/alert-circle";

const authStore = useAuthStore();
const items = createResource({
	url: "helpdesk.api.dashboard.get_all",
	auto: true,
});

const dateInfo =
	"📊 The information displayed in these charts are derived from data collected over the past 30 days";
</script>
