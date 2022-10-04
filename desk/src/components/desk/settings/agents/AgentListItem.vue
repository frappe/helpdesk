<template>
	<div
		class="block select-none rounded-[6px] py-[7px] px-[11px]"
		:class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'"
	>
		<div v-if="agent" role="button" class="flex items-center text-base">
			<div class="w-[37px] h-[14px] flex items-center">
				<Input
					type="checkbox"
					@click="$emit('toggleSelect')"
					:checked="selected"
					role="button"
				/>
			</div>
			<router-link
				:to="`/frappedesk/settings/agents/${agent.name}`"
				class="w-full group flex items-center"
			>
				<div class="sm:w-4/12 truncate pr-10">
					{{ agent.full_name }}
				</div>
				<div class="sm:w-5/12 truncate pr-10">
					{{ agent.email }}
				</div>
				<div class="sm:w-3/12 truncate pr-10">
					{{ agent.group }}
				</div>
				<div class="sm:w-2/12 truncate">
					<div class="w-full flex flex-row-reverse">
						<Badge v-if="agent.send_welcome_email" color="yellow">
							Pending
						</Badge>
					</div>
				</div>
			</router-link>
		</div>
	</div>
</template>

<script>
import { Input, FeatherIcon } from "frappe-ui"
import Badge from "frappe-ui/src/components/Badge.vue"

export default {
	name: "AgentListItem",
	props: ["agent", "selected"],
	components: {
		Input,
		FeatherIcon,
		Badge,
	},
}
</script>
