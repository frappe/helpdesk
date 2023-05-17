<template>
	<Popover>
		<template #target="{ togglePopover }">
			<IconAdd class="h-4 w-4 cursor-pointer" @click="togglePopover" />
		</template>
		<template #body-main>
			<div class="flex w-48 flex-col gap-2 p-3 text-base text-gray-800">
				<div
					v-for="column in keys(columns)"
					:key="column"
					class="flex items-center justify-between"
				>
					{{ column }}
					<MinimalSwitch
						:enabled="columns[column]"
						@click="toggleColumn(column)"
					/>
				</div>
			</div>
		</template>
	</Popover>
</template>

<script setup lang="ts">
import { Popover } from "frappe-ui";
import { keys } from "lodash";
import { useData } from "./data";
import MinimalSwitch from "@/components/MinimalSwitch.vue";
import IconAdd from "~icons/espresso/add";

const { columns } = useData();

function toggleColumn(column: string) {
	columns[column] = !columns[column];
}
</script>
