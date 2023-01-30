<template>
	<div class="flex flex-col my-[16px] px-2">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-center space-x-2">
				<CustomAvatar
					:label="userName"
					:imageURL="profilePicUrl"
					size="sm"
				/>
				<div
					class="truncate text-base max-w-[200px] text-gray-900 font-medium"
				>
					{{ userName }}
				</div>
			</div>
			<a
				:title="$dayjs(time)"
				class="text-gray-500 text-sm select-none font-normal"
				>{{ $dayjs.longFormating($dayjs(time).fromNow()) }}</a
			>
		</div>
		<div class="pl-8 pt-1.5">
			<div class="flex flex-col">
				<div
					class="message text-base"
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
							class="py-1 max-w-[180px] rounded-md border px-2 text-gray-700 font-normal text-sm hover:underline flex items-center space-x-2 border-gray-200 mr-[10px] mb-[5px]"
						>
							<FeatherIcon
								name="paperclip"
								class="h-3 w-3 shrink-0"
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
import CustomAvatar from "@/components/global/CustomAvatar.vue"
import { FeatherIcon } from "frappe-ui"
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

<style scoped>
.message >>> .content-block {
	@apply prose prose-p:my-1 prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100 max-w-full;
}
</style>
