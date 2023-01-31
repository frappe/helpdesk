<template>
	<div class="flex flex-col">
		<div class="flex border-b h-[52px] px-6 shrink-0">
			<div class="grow my-auto text-xl font-semibold text-gray-900">
				Contacts
			</div>
		</div>
		<div class="flex flex-row w-full h-full">
			<ContactInfo
				class="shrink-0 border-r border-gray-100"
				:contactId="contactId"
			/>
			<ContactRelatedInfo class="grow" :contact="contactId" />
		</div>
	</div>
</template>

<script>
import ContactInfo from "@/components/desk/contacts/ContactInfo.vue"
import ContactRelatedInfo from "@/components/desk/contacts/ContactRelatedInfo.vue"

export default {
	name: "Contact",
	props: ["contactId"],
	components: {
		ContactInfo,
		ContactRelatedInfo,
	},
}
</script>
