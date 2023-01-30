<template>
	<div
		v-if="activity"
		class="pb-5 space-x-[17.78px] flex flex-row select-none text-sm"
	>
		<div>
			<CustomIcons class="h-4 w-4" name="disc" />
			<div v-if="!isLast" class="h-full border-l mx-2" />
			<div v-if="!isLast" class="h-5 border-l mx-2" />
		</div>
		<div class="grow pr-1.5">
			<div class="flex flex-col text-gray-700">
				<div>
					<div class="font-normal">
						{{ capitalizeFirstLetter(activity.action) }}
					</div>
					<div class="flex flex-row space-x-1">
						<div>by</div>
						<div class="font-medium">{{ activity.owner }}</div>
					</div>
				</div>
				<a
					class="text-gray-600 text-xs text-normal"
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
	methods: {
		capitalizeFirstLetter(string) {
			return string.charAt(0).toUpperCase() + string.slice(1)
		},
	},
}
</script>
