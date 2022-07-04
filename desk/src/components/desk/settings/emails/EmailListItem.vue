<template>
	<div class="block select-none rounded-[6px] py-[7px] px-[11px]" :class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'">
		<div
			v-if="emailAccount"
			class="flex items-center text-base"
		>
			<div 
				class="w-[37px] h-[14px] flex items-center"
			>
				<Input
					type="checkbox" 
					@click="$emit('toggleSelect')" 
					:checked="selected" 
					role="button"
				/>
			</div>
            <div class="w-full group flex items-center">
				<router-link :to="`/frappedesk/settings/emails/${emailAccount.name}`" class="sm:w-4/12">
					{{ emailAccount.name }}
				</router-link>
				<div class="sm:w-5/12">
					{{ emailAccount.email_id }}
				</div>
				<div class="sm:w-3/12">
                    <div class="pl-4">
                        <a :title="emailAccount.default_incoming ? 'default incoming' : ''"><FeatherIcon v-if="emailAccount.enable_incoming" name="arrow-down-circle" class="w-5 h-5 stroke-2" :class="emailAccount.default_incoming ? 'stroke-blue-500' : 'stroke-gray-600'" /></a>
                    </div>
				</div>
                <div class="sm:w-3/12">
                    <div class="pl-4">
                        <a :title="emailAccount.default_outgoing ? 'default outging' : ''"><FeatherIcon v-if="emailAccount.enable_outgoing" name="arrow-up-circle" class="w-5 h-5 stroke-2" :class="emailAccount.default_outgoing ? 'stroke-blue-500' : 'stroke-gray-600'" /></a>
                    </div>
                </div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input, FeatherIcon } from 'frappe-ui'

export default {
	name: 'EmailListItem',
	props: ['emailAccount', 'selected'],
	components: {
		Input,
		FeatherIcon,
	}
}
</script>