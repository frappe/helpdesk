<template>
	<div
		v-if="comment"
		class="flex flex-col my-[16px] bg-[#FDF9F2] p-[10px] rounded-[6px]"
	>
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-center space-x-[8px]" v-if="user">
				<CustomAvatar
					:imageURL="user.user_image"
					:label="user.full_name"
					size="sm"
				/>
				<div class="flex flex-row space-x-1 items-center text-[13px]">
					<div class="truncate font-medium max-w-[200px]">
						{{ user.full_name }}
					</div>
					<div class="font-normal text-gray-900">added a comment</div>
				</div>
			</div>
			<div class="text-gray-500 font-normal text-[12px]">
				{{ $dayjs.longFormating($dayjs(comment.creation).fromNow()) }}
			</div>
		</div>
		<div class="pl-[32px] pt-[6px]">
			<div class="flex flex-col">
				<div
					class="ProseMirror prose prose-p:my-1 max-w-full text-[13px] text-gray-700"
					v-html="cleanedMessage"
				></div>
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
	props: ["comment"],
	components: {
		FeatherIcon,
		CustomAvatar,
	},
	computed: {
		cleanedMessage() {
			if (this.comment?.content) {
				return remove_script_and_style(this.comment.content)
			}
			return ""
		},
		user() {
			return this.$resources.user.data || null
		},
	},
	resources: {
		user() {
			return {
				method: "frappe.client.get",
				params: {
					doctype: "User",
					name: this.comment?.commented_by,
					fields: ["*"],
				},
				auto: true,
			}
		},
	},
}
</script>

<style>
.mention {
	color: #2490ef;
	font-weight: 500;
}
</style>
