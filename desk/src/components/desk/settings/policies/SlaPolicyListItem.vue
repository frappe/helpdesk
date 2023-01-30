<template>
	<div
		class="block select-none rounded-[6px] py-1.5 px-2.5"
		:class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'"
	>
		<div v-if="policy" role="button" class="flex items-center text-base">
			<div class="w-9 h-3.5 flex items-center">
				<Input
					type="checkbox"
					@click="$emit('toggleSelect')"
					:checked="selected"
					role="button"
				/>
			</div>
			<div class="w-full group flex items-center">
				<router-link
					:to="`/frappedesk/settings/sla/${policy.name}`"
					class="sm:w-10/12 truncate pr-10 flex flex-row items-center space-x-2"
				>
					<div>
						{{ policy.name }}
					</div>
					<a title="Default service level agreement">
						<CustomIcons
							v-if="policy.default_sla"
							name="circle-check"
							class="w-4 h-4 fill-blue-500"
						/>
					</a>
				</router-link>
				<div class="sm:w-2/12">
					<div class="flex flex-row-reverse">
						<CustomSwitch
							v-model="policy.enabled"
							:disabled="policy.default_sla"
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input, FeatherIcon } from "frappe-ui"
import CustomSwitch from "@/components/global/CustomSwitch.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "SlaPolicyListItem",
	props: ["policy", "selected"],
	components: {
		Input,
		FeatherIcon,
		CustomSwitch,
		CustomIcons,
	},
}
</script>
