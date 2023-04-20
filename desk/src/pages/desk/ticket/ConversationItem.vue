<template>
	<div class="my-2 flex rounded-lg py-2.5 px-2">
		<div class="ml-2 mr-3">
			<Avatar image-u-r-l="https://picsum.photos/200" size="md" />
		</div>
		<div class="flex flex-col gap-1">
			<div class="mb-8">
				<div class="flex items-center justify-between">
					<div class="flex items-center">
						<div class="text-base text-gray-900">Abhay Mukherjee</div>
						<IconDot class="text-gray-600" />
						<div class="text-sm text-gray-600">2:41 PM</div>
					</div>
					<Dropdown v-bind="dropdownOptions" />
				</div>
				<div class="flex gap-1">
					<div class="text-base text-gray-800">Cc:</div>
					<div class="text-base text-gray-700">Matt Daemon, Liam Smith</div>
				</div>
				<div class="flex gap-1">
					<div class="text-base text-gray-800">Bcc:</div>
					<div class="text-base text-gray-700">Matt Daemon, Liam Smith</div>
				</div>
			</div>
			<div class="text-base text-gray-700">
				Hi, The monthly statistics for February 2023 have been compiled and
				analysed. These statistics cover a range of areas, including sales
				figures, customer demographics, and market trends. Additionally, the
				customer demographics have been analysed to identify potential areas for
				growth and improvement.
				<br />
				<br />
				Thanks, Zach Micheal
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { Avatar, Dropdown } from "frappe-ui";
import IconDot from "~icons/ph/dot-outline-fill";

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
