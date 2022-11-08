<template>
	<div
		class="flex flex-row rounded bg-white shadow pl-1.5 pr-0.5 select-none text-gray-600"
	>
		<div class="py-0.5 px-1">fieldname</div>
		<div role="button" class="hover:bg-gray-100 border-x py-0.5 px-1">
			operator
		</div>
		<div role="button" class="hover:bg-gray-100 py-0.5 px-1">value</div>
		<div class="hover:bg-gray-100 p-1 rounded my-0.5" role="button">
			<FeatherIcon name="x" class="h-3 w-3" />
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"

export default {
	name: "FilterBoxItem",
	props: {
		filter: {
			type: Object,
			required: true,
		},
	},
	mounted() {
		// TODO: focus on input (fieldname input) if fieldname is empty
	},
	components: { FeatherIcon },
}
</script>
