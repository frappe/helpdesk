<template>
	<div class="py-3 space-x-2 flex">
		<div>
			<Avatar :label="userName" :imageURL="profilePicUrl" size="md" />
			<div v-if="!isLast" class="h-full border-l mx-4" />
		</div>
		<div class="grow space-y-2">
			<div class="flex space-x-2 items-center text-base">
				<div>{{ userName }}</div>
				<div class="text-slate-500">{{ `${$dayjs(time).fromNow()} (${$dayjs(time).format('ddd, MMM DD, YYYY H:m')})` }}</div>
			</div>
			<div class="rounded shadow p-3 bg-gray-100">
				<div v-html="message"></div>
			</div>
		</div>
	</div>
</template>

<script>
import { Avatar } from 'frappe-ui'

export default {
	name: 'ConversationCard',
	props: ['userName', 'profilePicUrl', 'time', 'message', 'isLast'],
	components: {
		Avatar
	}
}
</script>

<style>

</style>