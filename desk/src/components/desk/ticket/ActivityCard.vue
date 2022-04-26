<template>
	<div v-if="activity" class="py-[5px] space-x-[17.78px] flex select-none text-[12px]">
		<div>
			<CustomIcons class="h-4 w-4" name="disc" />
			<div v-if="!isLast" class="h-full border-l mx-2" />
		</div>
		<div class="grow space-y-2 pr-[6px]">
			<div class="flex flex-col">
				<div><span class="font-medium">{{ activity.owner }}</span> <span class="font-normal text-gray-700">{{ activity.action }}</span></div>
				<div class="text-gray-500">{{ $dayjs(activity.creation).fromNow() }}</div>
			</div>
		</div>
	</div>
</template>

<script>
import CustomIcons from '@/components/desk/global/CustomIcons.vue'

export default {
	name: 'ActivityCard',
	components: {
		CustomIcons
	},
	props: ['activity', 'isLast'],
}
</script>

<style>

</style>