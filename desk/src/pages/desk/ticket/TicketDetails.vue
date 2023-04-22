<template>
	<div class="flex flex-col">
		<div class="border-l">
			<div class="m-4">
				<div class="flex items-center justify-between">
					<div class="text-lg font-semibold text-gray-900">Ticket details</div>
					<Button icon="x" appearance="minimal" />
				</div>
				<div class="my-6 flex flex-col justify-between gap-3.5">
					<div class="flex justify-between">
						<div class="text-xs text-gray-600">Customer:</div>
						<div class="flex items-center gap-1">
							<Avatar
								image-u-r-l="https://picsum.photos/200"
								label="foobar"
								size="sm"
							/>
							<div class="text-xs font-medium text-gray-700">Zach Micheal</div>
						</div>
					</div>
					<div class="flex justify-between">
						<div class="text-xs text-gray-600">First response Due:</div>
						<div class="text-xs font-medium text-gray-700">
							March 12, 2:24 PM
						</div>
					</div>
					<div class="flex justify-between">
						<div class="text-xs text-gray-600">Resolution Due:</div>
						<div class="text-xs font-medium text-gray-700">
							April 9, 12:20 PM
						</div>
					</div>
				</div>
			</div>
		</div>
		<div class="divider"></div>
		<div
			class="flex grow flex-col gap-3 truncate border-l p-4"
			:style="{
				'overflow-y': 'scroll',
			}"
		>
			<div class="flex flex-col gap-1">
				<div class="text-xs text-gray-600">Assigned To</div>
				<Autocomplete placeholder="Select an agent" />
			</div>
			<div class="flex flex-col gap-1">
				<div class="text-xs text-gray-600">Ticket Type</div>
				<Autocomplete placeholder="Select a ticket type" />
			</div>
			<div class="flex gap-2">
				<div class="flex w-1/2 flex-col gap-1">
					<div class="text-xs text-gray-600">Priority</div>
					<Autocomplete placeholder="High" />
				</div>
				<div class="flex w-1/2 flex-col gap-1">
					<div class="text-xs text-gray-600">Status</div>
					<Autocomplete placeholder="Open" />
				</div>
			</div>
			<div class="flex flex-col gap-1">
				<div class="text-xs text-gray-600">Team</div>
				<Autocomplete placeholder="Select a team" />
			</div>
		</div>
		<div class="border-l">
			<div
				class="mx-4 my-3.5 flex h-8 cursor-pointer items-center justify-center rounded-lg bg-gray-100 px-3 py-2 hover:bg-gray-200"
			>
				<div class="text-base text-gray-800">Save</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { Autocomplete, Avatar, Button } from "frappe-ui";
</script>

<style scoped>
.divider {
	border-bottom: 1px solid #e2e2e2;
	border-style: dashed;
	position: relative;
}

.divider:before {
	position: absolute;
	bottom: -14px;
	left: 0;
	height: 28px;
	width: 14px;
	background: white;
	content: "";
	border-top-right-radius: 9999px;
	border-bottom-right-radius: 9999px;
	border-right-width: 1px;
	border-top-width: 1px;
	border-bottom-width: 1px;
}

.divider:after {
	position: absolute;
	bottom: -14px;
	left: 0;
	height: 28px;
	width: 14px;
	background: white;
	content: "";
	border-top-left-radius: 9999px;
	border-bottom-left-radius: 9999px;
	border-left-width: 1px;
	border-top-width: 1px;
	border-bottom-width: 1px;
}

.divider:after {
	right: 0;
	left: auto;
}
</style>
