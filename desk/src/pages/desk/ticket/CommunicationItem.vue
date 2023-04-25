<template>
	<div class="group flex gap-3">
		<div class="flex w-8 justify-end">
			<Avatar :image-u-r-l="senderImage" size="md" />
		</div>
		<div class="flex w-full flex-col gap-1">
			<div class="flex items-start justify-between">
				<div class="flex items-center">
					<div class="text-base text-gray-900">{{ sender }}</div>
					<IconDot class="text-gray-600" />
					<div class="text-sm text-gray-600">{{ dateDisplay }}</div>
				</div>
				<Dropdown :options="options">
					<template #default>
						<FeatherIcon
							name="more-horizontal"
							class="h-5 w-5 cursor-pointer opacity-0 group-hover:opacity-100"
						/>
					</template>
				</Dropdown>
			</div>
			<div v-if="cc || bcc" class="flex gap-1 text-xs text-gray-600">
				<div class="font-medium">cc:</div>
				{{ cc }},
				<div class="font-medium">bcc:</div>
				{{ bcc }}
			</div>
			<div class="prose max-w-none text-base text-gray-700">
				<!-- This is vulnerable to attacks. Prefer markdown wherever possible. -->
				<!-- eslint-disable-next-line vue/no-v-html -->
				<span v-html="content"></span>
			</div>
			<div class="flex flex-wrap gap-2">
				<div
					v-for="attachment in attachments"
					:key="attachment.file_url"
					class="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 p-1 shadow"
				>
					<div class="flex flex-row items-center space-x-1">
						<FeatherIcon name="file-text" class="h-4 w-4 text-gray-700" />
						<a
							:href="attachment.file_url"
							target="_blank"
							class="text-sm text-gray-700"
						>
							{{ attachment.file_name }}
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { toRefs } from "vue";
import dayjs from "dayjs";
import { Avatar, Dropdown, FeatherIcon } from "frappe-ui";
import { editor } from "./data";
import IconDot from "~icons/ph/dot-bold";

type Attachment = {
	file_name: string;
	file_url: string;
};

const props = defineProps({
	content: {
		type: String,
		required: true,
	},
	date: {
		type: String,
		required: true,
	},
	sender: {
		type: String,
		required: true,
	},
	senderImage: {
		type: String,
		required: false,
		default: "",
	},
	cc: {
		type: String,
		required: false,
		default: "",
	},
	bcc: {
		type: String,
		required: false,
		default: "",
	},
	attachments: {
		type: Array<Attachment>,
		required: false,
		default: [],
	},
});

const { content, date, sender, senderImage, cc, bcc } = toRefs(props);
const dateDisplay = dayjs(date.value).format("h:mm A");
const options = [
	{
		label: "Reply",
		handler: () => {
			editor.cc = [];
			editor.bcc = [];
			editor.content = quote(content.value);
			editor.isExpanded = true;
		},
	},
	{
		label: "Reply All",
		handler: () => {
			editor.cc = cc.value?.split(",");
			editor.bcc = bcc.value?.split(",");
			editor.content = quote(content.value);
			editor.isExpanded = true;
		},
	},
];

function quote(s: string) {
	return `<blockquote>${s}</blockquote><br/>`;
}
</script>
