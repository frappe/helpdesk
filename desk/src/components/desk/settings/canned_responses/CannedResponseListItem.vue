<template>
	<div
		class="block select-none rounded-md py-1.5 px-2.5"
		:class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'"
	>
		<div
			v-if="canned_response"
			role="button"
			class="flex items-center text-base"
		>
			<div class="w-9 h-3.5 flex items-center">
				<Input
					type="checkbox"
					@click="$emit('toggleSelect')"
					:checked="selected"
					role="button"
				/>
			</div>
			<router-link
				:to="`/frappedesk/settings/canned_responses/${canned_response.name}`"
				class="w-full group flex items-center"
			>
				<div class="sm:w-10/12 truncate pr-10">
					{{ canned_response.title }}
				</div>
				<div class="sm:w-2/12 truncate pr-10">
					{{ canned_response.owner }}
				</div>
				<div class="sm:w-2/12 truncate"></div>
			</router-link>
		</div>
	</div>
</template>

<script>
import { Input, FeatherIcon } from "frappe-ui"
import Badge from "frappe-ui/src/components/Badge.vue"
export default {
	name: "CannedResponseListItem",
	props: ["canned_response", "selected"],
	components: {
		Input,
		FeatherIcon,
		Badge,
	},
}
</script>
