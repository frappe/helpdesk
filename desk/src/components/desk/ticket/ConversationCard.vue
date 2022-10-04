<template>
	<div class="flex flex-col my-[16px] px-[10px]">
		<div class="flex flex-row justify-between">
			<div class="flex flex-row items-center space-x-[8px]">
				<CustomAvatar
					:label="userName"
					:imageURL="profilePicUrl"
					size="sm"
				/>
				<div class="truncate text-[14px] font-normal max-w-[200px]">
					{{ userName }}
				</div>
			</div>
			<a
				:title="$dayjs(time)"
				class="text-gray-500 text-[12px] select-none"
				>{{ $dayjs.longFormating($dayjs(time).fromNow()) }}</a
			>
		</div>
		<div class="pl-[32px] pt-[6px]">
			<div class="flex flex-col">
				<div
					class="prose prose-p:my-1 text-[13px] text-gray-700"
					style="border: 0px"
					v-html="cleanedMessage"
				></div>
				<div
					v-if="attachments.length > 0"
					class="flex flex-wrap text-base mt-[8px]"
				>
					<div v-for="attachment in attachments" :key="attachment">
						<a
							:href="attachment.file_url"
							target="_blank"
							class="py-[4px] max-w-[180px] rounded-[6px] border px-[8px] text-gray-700 font-normal text-[12px] hover:underline flex items-center space-x-[8px] border-gray-200 mr-[10px] mb-[5px]"
						>
							<FeatherIcon
								name="paperclip"
								class="h-[12px] w-[12px] shrink-0"
							/>
							<span class="truncate">{{
								attachment.file_name
							}}</span>
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"
import CustomAvatar from "@/components/global/CustomAvatar.vue"
import { remove_script_and_style } from "@/utils"

export default {
	name: "ConversationCard",
	props: [
		"userName",
		"profilePicUrl",
		"time",
		"message",
		"color",
		"attachments",
	],
	components: {
		FeatherIcon,
		CustomAvatar,
	},
	computed: {
		cleanedMessage() {
			if (this.message) {
				return remove_script_and_style(this.message)
			}
			return ""
		},
	},
}
</script>

<style></style>
