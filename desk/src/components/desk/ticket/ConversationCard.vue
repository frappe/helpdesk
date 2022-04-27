<template>
	<div class="flex flex-col my-[24px]">
		<div class="flex flex-row justify-between">
			<div class="flex flex-row items-center space-x-[8px]">
				<CustomAvatar :label="userName" :imageURL="profilePicUrl" size="sm" />
				<div class="truncate text-[14px] font-normal max-w-[200px]">{{ userName }}</div>
			</div>
			<div class="text-gray-500 text-[12px]">{{ $dayjs.longFormating($dayjs(time).fromNow()) }}</div>
		</div>
		<div class="pl-[32px] pt-[6px]">
			<div class="flex flex-col">
				<div class="ql-container text-[13px] text-gray-700" v-html="cleanedMessage"></div>
				<div v-if="attachments.length > 0" class="flex space-x-2 flex-wrap text-base mt-3">
					<div v-for="attachment in attachments" :key="attachment">
						<a :href="attachment.file_url" class="py-1 rounded-sm text-gray-900 hover:underline flex items-center space-x-1">
							<FeatherIcon name="file" class="h-3 w-3" />
							<span>{{ attachment.file_name }}</span>
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import CustomAvatar from '@/components/global/CustomAvatar.vue'
import { remove_script_and_style } from '@/utils'

export default {
	name: 'ConversationCard',
	props: ['userName', 'profilePicUrl', 'time', 'message', 'isLast', 'color', 'attachments'],
	components: {
		FeatherIcon,
		CustomAvatar
	},
	computed: {
		cleanedMessage() {
			if (this.message) {
				return remove_script_and_style(this.message)
			}
			return ''
		}
	}
}
</script>

<style>

</style>