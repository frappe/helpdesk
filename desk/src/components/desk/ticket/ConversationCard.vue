<template>
	<div class="py-3 space-x-2 flex">
		<div>
			<Avatar :label="userName" :imageURL="profilePicUrl" size="md" />
			<div v-if="!isLast" class="h-full border-l mx-4" />
		</div>
		<div class="grow space-y-2">
			<div class="flex space-x-2 items-center text-base">
				<div class="truncate max-w-[200px]">{{ userName }}</div>
				<div class="text-slate-500">{{ `${$dayjs(time).fromNow()} (${$dayjs(time).format('ddd, MMM DD, YYYY H:m')})` }}</div>
			</div>
			<div class="rounded shadow p-3" :class="`bg-${color}-50`">
				<div class="ql-container" v-html="cleanedMessage"></div>
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
import { Avatar, FeatherIcon } from 'frappe-ui'
import { remove_script_and_style } from '@/utils'

export default {
	name: 'ConversationCard',
	props: ['userName', 'profilePicUrl', 'time', 'message', 'isLast', 'color', 'attachments'],
	components: {
		Avatar,
		FeatherIcon
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