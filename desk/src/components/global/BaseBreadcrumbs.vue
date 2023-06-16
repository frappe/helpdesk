<template>
	<div class="flex flex-row space-x-2 items-center text-gray-600 text-base">
		<div v-for="(breadcrumb, index) in breadcrumbs" :key="breadcrumb">
			<div class="flex flex-row items-center space-x-2">
				<div
					@click="
						() => {
							if (breadcrumb.onClick) {
								breadcrumb.onClick()
							}
							$emit('item-click', breadcrumb, index)
						}
					"
					:class="
						!isBreadcrumbLast(index) && interactable
							? 'cursor-pointer hover:text-gray-900'
							: ''
					"
				>
					{{ breadcrumb.label }}
				</div>
				<div v-if="!isBreadcrumbLast(index)">
					<FeatherIcon
						class="h-3 w-3 stroke-gray-500"
						name="chevron-right"
					/>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"

export default {
	name: "BaseBreadcrumbs",
	props: {
		breadcrumbs: {
			type: Array,
			default: () => [],
		},
		interactable: {
			type: Boolean,
			default: true,
		},
	},
	components: {
		FeatherIcon,
	},
	methods: {
		isBreadcrumbLast(index) {
			return index === this.breadcrumbs.length - 1
		},
	},
}
</script>
