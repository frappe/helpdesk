<template>
	<div class="flex flex-col border-l">
		<div class="mx-4 mt-4">
			<div class="flex items-center justify-between">
				<div class="text-lg font-semibold text-gray-800">Contact details</div>
				<Button
					appearance="minimal"
					icon="x"
					@click="sidebar.isExpanded = false"
				/>
			</div>
			<div class="flex items-center gap-3 border-b py-6">
				<Avatar
					:image-u-r-l="c.doc?.image"
					:label="c.doc?.full_name"
					size="lg"
				/>
				<div class="flex flex-col">
					<div class="text-lg font-semibold text-gray-800">
						{{ c.doc?.full_name }}
					</div>
					<div class="text-base text-gray-600">
						{{ c.doc?.company_name }}
					</div>
				</div>
			</div>
		</div>
		<div class="overflow-auto px-4">
			<div
				v-if="!isEmpty(contactOptions)"
				class="flex flex-col gap-3.5 border-b py-6 text-base"
			>
				<div
					v-for="contact in contactOptions"
					:key="contact.name"
					class="flex items-start gap-2"
				>
					<div class="h-5 w-5">
						<component :is="contact.icon" class="h-5 w-5 text-gray-600" />
					</div>
					<div class="text-gray-900">{{ contact.value }}</div>
				</div>
			</div>
			<CustomFieldList />
			<OpenTicketList />
		</div>
	</div>
</template>

<script setup lang="ts">
import { isEmpty } from "lodash";
import { computed } from "vue";
import { Avatar, Button, createDocumentResource } from "frappe-ui";
import { useTicketStore } from "./data";
import CustomFieldList from "./CustomFieldList.vue";
import OpenTicketList from "./OpenTicketList.vue";
import IconEmail from "~icons/espresso/email";

const { sidebar, ticket } = useTicketStore();

const c = createDocumentResource({
	doctype: "Contact",
	name: ticket.doc.contact,
	auto: true,
});

const fields = [
	{
		field: "email_id",
		icon: IconEmail,
	},
];

const contactOptions = computed(() =>
	fields
		.map((o) => ({ name: o.field, value: c.doc?.[o.field], icon: o.icon }))
		.filter((o) => o.value)
);
</script>
