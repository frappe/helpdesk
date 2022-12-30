<template>
	<div v-if="contact" class="space-y-[12px]">
		<div class="flex flex-row items-center space-x-[12px]">
			<CustomAvatar
				:label="contactFullName"
				:imageURL="contact?.image"
				size="md"
				class="ml-[-6.5px]"
			/>
			<a
				:title="contactFullName"
				class="grow truncate font-normal text-base"
				>{{ contactFullName }}</a
			>
		</div>
		<div
			v-if="contact.phone_nos.length > 0"
			class="flex space-x-[12px] items-center"
		>
			<FeatherIcon
				name="phone"
				class="stroke-gray-500"
				style="width: 15px"
			/>
			<div
				class="space-y-1"
				v-for="phone_no in contact.phone_nos"
				:key="phone_no"
			>
				<a :title="phone_no.phone" class="text-gray-700 text-base">{{
					phone_no.phone
				}}</a>
			</div>
		</div>
		<div v-if="contact.email_ids.length > 0" class="flex space-x-[12px]">
			<FeatherIcon
				name="mail"
				class="stroke-gray-500 mt-[2.5px]"
				style="width: 15px; height: 15px"
			/>
			<div
				class="space-y-1 max-w-[173px] break-words"
				v-for="email in contact.email_ids"
				:key="email"
			>
				<div :title="email.email_id" class="text-gray-700 text-base">
					<a :title="email.email_id">{{ email.email_id }}</a>
				</div>
			</div>
		</div>
		<div v-if="contact.links.length > 0" class="flex space-x-[12px]">
			<CustomIcons
				name="customer"
				class="stroke-gray-500 mt-[2.5px]"
				style="width: 15px; height: 15px"
			/>
			<div
				class="space-y-1 max-w-[173px] break-words"
				v-for="link in contact.links"
				:key="link"
			>
				<div class="text-gray-700 text-base">
					<a
						:title="link.link_title"
						class="grow truncate font-normal text-base"
						>{{ link.link_title }}</a
					>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"
import CustomAvatar from "@/components/global/CustomAvatar.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "ContactInfo",
	props: ["contactId"],
	components: {
		FeatherIcon,
		CustomAvatar,
		CustomIcons,
	},
	computed: {
		contact() {
			return this.$resources.contact.doc || null
		},
		contactFullName() {
			if (this.contact) {
				return (
					(this.contact.first_name || "") +
					" " +
					(this.contact.last_name || "")
				).slice(0, 40)
			}
		},
	},
	resources: {
		contact() {
			return {
				type: "document",
				doctype: "Contact",
				name: this.contactId,
			}
		},
	},
}
</script>
