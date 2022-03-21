<template>
	<div class="flex mt-5">
		<Avatar :label="userName" :imageURL="profilePicUrl" size="md" />
		<div class="w-full mx-2 pt-1">
			<div class="flex justify-between">
				<div class="text-lg">{{ userName }}</div>
				<div class="text-sm text-slate-500">{{ $dayjs(time).fromNow() }}</div>
			</div>
			<div class="grow rounded p-2 text-base mt-2" :class="`bg-${color}-50`">
				<span v-html="cleanedMessage"></span>
			</div>
		</div>
	</div>
</template>

<script>
import { Avatar } from 'frappe-ui'
import { remove_script_and_style } from '@/utils'

export default {
	name: 'ConversationCard',
	props: ['userName', 'profilePicUrl', 'time', 'message', 'color'],
	components: {
		Avatar
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