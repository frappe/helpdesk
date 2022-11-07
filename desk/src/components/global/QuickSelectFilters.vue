<template>
	<Dropdown placement="left">
		<template v-slot="{ toggleDropdown }">
			<div
				class="flex flex-row items-center space-x-1 cursor-pointer select-none"
				@click="toggleDropdown"
			>
				<div class="text-lg font-semibold">
					{{
						`All ${manager.options.doctype}s (${manager.totalCount})`
					}}
				</div>
				<FeatherIcon name="chevron-down" class="h-4 w-4 stroke-2" />
			</div>
		</template>
	</Dropdown>
</template>

<script>
import { Dropdown, FeatherIcon } from "frappe-ui"

export default {
	name: "QuickSelectFilters",
	components: {
		Dropdown,
		FeatherIcon,
	},
	inject: ["manager"],
	computed: {
		options() {},
	},
	resources: {},
}
</script>
