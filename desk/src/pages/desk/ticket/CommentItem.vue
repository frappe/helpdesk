<template>
	<div class="group my-2 flex rounded-lg bg-gray-50 py-2.5 px-2">
		<div class="ml-2 mr-3">
			<Avatar :image-u-r-l="sender.user_image" size="md" />
		</div>
		<div class="flex w-full flex-col gap-1">
			<div class="flex items-center justify-between">
				<div class="flex items-center">
					<div class="text-base text-gray-900">{{ sender.full_name }}</div>
					<IconDot class="text-gray-600" />
					<div class="text-sm text-gray-600">{{ dateDisplay }}</div>
				</div>
				<Dropdown
					v-if="!isEmpty(dropdownOptions.options)"
					v-bind="dropdownOptions"
					class="opacity-0 group-hover:opacity-100"
				/>
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
import { PropType, reactive, toRefs } from "vue";
import { Avatar, createResource, Dropdown } from "frappe-ui";
import { isEmpty } from "lodash";
import dayjs from "dayjs";
import { useAuthStore } from "@/stores/auth";
import { createToast } from "@/utils/toasts";
import IconDot from "~icons/ph/dot-outline-fill";

type Sender = {
	name: string;
	full_name: string;
	user_image: string;
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
	name: {
		type: String,
		required: true,
	},
	sender: {
		type: Object as PropType<Sender>,
		required: true,
	},
});
const { content, date, name, sender } = toRefs(props);
const authStore = useAuthStore();
const dateDisplay = dayjs(date.value).format("h:mm A");
const dropdownOptions = reactive({
	button: {
		appearance: "minimal",
		icon: "more-horizontal",
	},
	options: [],
});

function deleteComment() {
	createResource({
		url: "frappe.client.delete",
		params: {
			doctype: "HD Ticket Comment",
			name: name.value,
		},
		auto: true,
		onSuccess() {
			createToast({
				title: "Comment deleted",
				icon: "check",
				iconClasses: "text-green-500",
			});
		},
	});
}

if (sender.value.name === authStore.userId) {
	dropdownOptions.options.push({
		label: "Delete",
		handler: () => deleteComment(),
	});
}
</script>
