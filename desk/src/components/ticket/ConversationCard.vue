<template>
	<div class="py-5 border-b space-y-2">
		<div class="flex space-x-2 items-center">
			<Avatar :label="userName" :imageURL="profilePicUrl" size="md" />
			<div>
				<div class="text-lg">{{ userName }}</div>
				<div class="text-sm text-slate-500">{{ `${$dayjs(time).fromNow()} (${$dayjs(time).format('ddd, MMM DD, YYYY H:m')})` }}</div>
			</div>
		</div>
		<div class="grow">
			<div v-html="message"></div>
		</div>
	</div>
</template>

<script>
import { Avatar } from 'frappe-ui'

export default {
	name: 'ConversationCard',
	props: ['userName', 'profilePicUrl', 'time', 'message'],
	components: {
		Avatar
	}
}
</script>

<style>

</style>