<template>
	<div
		class="block select-none rounded-[6px] py-[7px] px-[11px]"
		:class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'"
	>
		<div v-if="contact" role="button" class="flex items-center text-base">
			<div class="w-[37px] h-[14px] flex items-center">
				<Input
					type="checkbox"
					@click="$emit('toggleSelect')"
					:checked="selected"
					role="button"
				/>
			</div>
			<router-link
				:to="`/frappedesk/contacts/${contact.name}`"
				class="w-full group flex items-center"
			>
				<div class="sm:w-5/12 truncate pr-10">
					{{ fullName }}
				</div>
				<div class="sm:w-6/12 truncate pr-10">
					<div v-if="contact.email && contact.email.length > 0">
						{{ contact.email }}
					</div>
				</div>
				<div class="sm:w-3/12 truncate pr-10">
					<div v-if="contact.phone && contact.phone.length > 0">
						{{ contact.phone }}
					</div>
				</div>
			</router-link>
		</div>
	</div>
</template>

<script>
import { computed } from "vue"
import { Input, FeatherIcon } from "frappe-ui"

export default {
	name: "ContactListItem",
	props: ["contact", "selected"],
	components: {
		Input,
		FeatherIcon,
	},
	setup(props) {
		const fullName = computed(() => {
			if (props.contact) {
				return (
					(props.contact.first_name || "") +
					" " +
					(props.contact.last_name || "")
				)
			}
		})

		return {
			fullName,
		}
	},
}
</script>
