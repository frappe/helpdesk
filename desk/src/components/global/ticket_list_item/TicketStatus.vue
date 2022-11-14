<template>
	<div class="flex flex-row items-center space-x-1">
		<FeatherIcon
			v-if="value != 'Open'"
			:name="
				{
					Closed: 'lock',
					Resolved: 'check',
					Replied: 'corner-up-left',
				}[value]
			"
			class="stroke-gray-600 w-[12px] h-[12px] mx-[2px]"
		/>
		<CustomIcons
			v-else
			name="comment"
			class="w-[16px] h-[16px] stroke-green-600"
		/>
		<div
			class="text-base font-normal"
			:class="{
				'text-green-600': value == 'Open',
				'text-gray-600': value != 'Open',
			}"
		>
			{{ value }}
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { FeatherIcon } from "frappe-ui"
export default {
	name: "TicketStatus",
	props: {
		value: {
			type: String,
			required: true,
		},
	},
	components: {
		CustomIcons,
		FeatherIcon,
	},
}
</script>
