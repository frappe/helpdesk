<template>
	<div
		v-if="activity"
		class="pb-[20px] space-x-[17.78px] flex flex-row select-none text-[12px]"
	>
		<div>
			<CustomIcons class="h-4 w-4" name="disc" />
			<div v-if="!isLast" class="h-full border-l mx-2" />
			<div v-if="!isLast" class="h-[20px] border-l mx-2" />
		</div>
		<div class="grow pr-[6px]">
			<div class="flex flex-col text-gray-700">
				<div>
					<span class="font-medium">{{ activity.owner }}</span>
					<span class="font-normal">{{ activity.action }}</span>
				</div>
				<a
					class="text-gray-600 text-[11px]"
					:title="$dayjs(activity.creation)"
					>{{
						$dayjs.longFormating(
							$dayjs(activity.creation).fromNow()
						)
					}}</a
				>
			</div>
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "ActivityCard",
	components: {
		CustomIcons,
	},
	props: ["activity", "isLast"],
}
</script>

<style></style>
