<template>
	<div class="py-2 space-x-2 flex">
		<div>
			<FeatherIcon class="fill-white stroke-slate-500 mx-2 h-4 w-4" name="disc" />
			<div v-if="!isLast" class="h-full border-l mx-4" />
		</div>
		<div class="grow space-y-2">
			<div class="flex space-x-2 items-center text-base">
				<div>{{ action }} by {{ owner }}</div>
				<div class="text-slate-500">{{ $dayjs(creation).fromNow() }}</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'

export default {
	name: 'ActivityCard',
	components: {
		FeatherIcon
	},
	props: ['action', 'owner', 'creation', 'isLast'],
}
</script>

<style>

</style>