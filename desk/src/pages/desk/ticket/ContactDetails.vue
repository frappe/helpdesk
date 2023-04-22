<template>
	<div class="flex flex-col border-l">
		<div class="m-4">
			<div class="flex items-center justify-between">
				<div class="text-lg font-semibold text-gray-800">Contact details</div>
				<Button appearance="minimal" icon="x" />
			</div>
			<div class="flex items-center gap-3 border-b py-6">
				<Avatar image-u-r-l="https://picsum.photos/200" size="lg" />
				<div class="flex flex-col gap-1.5">
					<div class="text-lg font-semibold text-gray-800">Zach Micheal</div>
					<div class="text-base text-gray-600">Sanfransico, CA</div>
				</div>
			</div>
		</div>
		<div class="overflow-scroll px-4">
			<div
				v-if="!isEmpty(contacts)"
				class="flex flex-col gap-3.5 border-b py-6 text-base"
			>
				<div
					v-for="contact in contacts"
					:key="contact.name"
					class="flex items-start gap-2"
				>
					<div class="h-5 w-5">
						<component :is="contact.icon" class="h-5 w-5 text-gray-600" />
					</div>
					<div class="text-gray-900">{{ contact.value }}</div>
				</div>
			</div>
			<div
				v-if="!isEmpty(customFields)"
				class="flex flex-col gap-5 border-b py-4"
			>
				<div
					v-for="field in customFields"
					:key="field.label"
					class="flex flex-col gap-2.5"
				>
					<div class="text-base text-gray-600">{{ field.label }}</div>
					<a :href="field.route" target="_blank">
						<div class="flex items-center gap-2">
							<div class="flex h-5 w-5 items-center justify-center">
								<IconWebLink v-if="field.route" class="h-5 w-5 text-gray-600" />
								<IconTeams v-else class="h-5 w-5 text-gray-600" />
							</div>
							<div class="text-base text-gray-800">{{ field.value }}</div>
						</div>
					</a>
				</div>
			</div>
			<div
				class="select-none py-4"
				:class="{
					'border-b': !isOpenTicketsVisible,
				}"
			>
				<div
					class="flex cursor-pointer items-center justify-between"
					@click="isOpenTicketsVisible = !isOpenTicketsVisible"
				>
					<div class="text-base font-medium text-gray-800">Open tickets</div>
					<IconCaretUp
						v-if="isOpenTicketsVisible"
						class="h-4 w-4 text-gray-600"
					/>
					<IconCaretDown v-else class="h-4 w-4 text-gray-600" />
				</div>
				<div v-if="isOpenTicketsVisible" class="flex flex-col gap-2 pt-4">
					<div v-for="field in openTickets" :key="field.name">
						<a :href="field.url" target="_blank" class="flex items-start gap-2">
							<div class="flex h-5 w-5 items-center justify-center">
								<IconWebLink class="h-5 w-5 text-gray-600" />
							</div>
							<div class="text-base text-gray-800">{{ field.title }}</div>
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { isEmpty } from "lodash";
import { ref } from "vue";
import { Avatar, Button } from "frappe-ui";
import IconCall from "~icons/espresso/call";
import IconEmail from "~icons/espresso/email";
import IconLocation from "~icons/espresso/location";
import IconTeams from "~icons/espresso/teams";
import IconWebLink from "~icons/espresso/web-link";
import IconCaretDown from "~icons/ph/caret-down";
import IconCaretUp from "~icons/ph/caret-up";

const isOpenTicketsVisible = ref(false);

const contacts = [
	{
		name: "phone",
		value: "603-555-0123",
		icon: IconCall,
	},
	{
		name: "email",
		value: "stacywall@gmail.com",
		icon: IconEmail,
	},
	{
		name: "address",
		value: "4140 Parker Rd. Allentown, New Mexico 31134",
		icon: IconLocation,
	},
];

const customFields = [
	{
		label: "Site",
		value: "example.frappe.cloud",
		route: "https://example.frappe.cloud",
	},
	{
		label: "Team",
		value: "Example Team",
	},
];

const openTickets = [
	{
		name: 1,
		title: "Ticket #1",
		url: "https://example.frappe.cloud/",
	},
	{
		name: 2,
		title: "Ticket #2",
		url: "https://example.frappe.cloud/",
	},
	{
		name: 3,
		title: "Ticket #3",
		url: "https://example.frappe.cloud/",
	},
	{
		name: 4,
		title: "A long ticket name that might be multiple lines long",
		url: "https://example.frappe.cloud/",
	},
];
</script>
