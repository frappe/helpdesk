<template>
	<div class="flex mt-5">
		<Avatar :label="userName" :imageURL="profilePicUrl" size="md" />
		<div class="w-full ml-2 pt-1">
			<div class="flex justify-between">
				<div class="text-lg">{{ userName }}</div>
				<div class="text-sm text-slate-500">
					{{ $dayjs.longFormating($dayjs(time).fromNow()) }}
				</div>
			</div>
			<div
				class="grow rounded p-2 text-base mt-2"
				:class="`bg-${color}-50`"
			>
				<div
					class="prose prose-p:my-1 text-[13px] text-gray-700"
					style="border: 0px"
					v-html="cleanedMessage"
				></div>
				<div
					v-if="attachments.length > 0"
					class="flex space-x-2 flex-wrap mt-3"
				>
					<div v-for="attachment in attachments" :key="attachment">
						<a
							:href="attachment.file_url"
							target="_blank"
							class="py-1 rounded-sm text-gray-900 hover:underline flex items-center space-x-1"
						>
							<FeatherIcon
								name="paperclip"
								class="h-[12px] w-[12px]"
							/>
							<span>{{ attachment.file_name }}</span>
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Avatar, FeatherIcon } from "frappe-ui"
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
		Avatar,
		FeatherIcon,
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
