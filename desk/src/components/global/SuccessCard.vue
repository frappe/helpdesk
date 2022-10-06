<template>
	<div
		class="flex flex-col items-center rounded-md p-10 text-base bg-green-50"
	>
		<FeatherIcon
			name="check-circle"
			class="stroke-green-500 stroke-2 h-20 w-20"
		/>
		<h2 class="mt-4 text-lg font-medium text-gray-900">
			{{ title }}
		</h2>
		<p class="mt-1.5 text-center text-base text-gray-700">
			<slot></slot>
		</p>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"

export default {
	name: "SuccessCard",
	props: ["title", "message"],
	components: {
		FeatherIcon,
	},
}
</script>
