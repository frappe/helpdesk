<template>
	<div class="my-2 flex rounded-lg py-2.5 px-2">
		<div class="ml-2 mr-3">
			<Avatar :image-u-r-l="senderImage" size="md" />
		</div>
		<div class="flex w-full flex-col gap-1">
			<div>
				<div class="flex items-center justify-between">
					<div class="flex items-center">
						<div class="text-base text-gray-900">{{ sender }}</div>
						<IconDot class="text-gray-600" />
						<div class="text-sm text-gray-600">{{ dateDisplay }}</div>
					</div>
					<Dropdown v-bind="dropdownOptions" />
				</div>
				<div v-if="cc || bcc" class="mb-2">
					<div v-if="cc" class="flex gap-1">
						<div class="text-base text-gray-800">Cc:</div>
						<div class="text-base text-gray-700">{{ cc }}</div>
					</div>
					<div v-if="bcc" class="flex gap-1">
						<div class="text-base text-gray-800">Bcc:</div>
						<div class="text-base text-gray-700">{{ bcc }}</div>
					</div>
				</div>
			</div>
			<div class="text-base text-gray-700">
				<!-- This is vulnerable to attacks. Prefer markdown wherever possible. -->
				<!-- eslint-disable-next-line vue/no-v-html -->
				<span v-html="content"></span>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, toRefs } from "vue";
import dayjs from "dayjs";
import { Avatar, Dropdown } from "frappe-ui";
import IconDot from "~icons/ph/dot-outline-fill";

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
});

const { content, date, sender, senderImage, cc, bcc } = toRefs(props);
const dateDisplay = dayjs(date.value).format("h:mm A");
const dropdownOptions = {
	button: {
		appearance: "minimal",
		icon: "more-horizontal",
	},
	options: [
		{
			label: "Reply",
			handler: () => console.log("foobar"),
		},
		{
			label: "Reply All",
			handler: () => console.log("foobar"),
		},
	],
};
</script>
