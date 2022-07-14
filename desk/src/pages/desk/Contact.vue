<template>
	<div class="flex flex-col">
		<div class="flex border-b h-[52px] px-[24px] shrink-0">
			<div class="grow my-auto text-[16px] font-semibold text-gray-900">
				Contacts
			</div>
		</div>
		<div class="flex flex-row w-full h-full">
			<ContactInfo class="shrink-0 border-r border-[#F4F5F6]" :contact="contactId" />
			<ContactRelatedInfo class="grow" :contact="contactId"/>
		</div>
	</div>
</template>

<script>
import ContactInfo from '@/components/desk/contacts/ContactInfo.vue'
import ContactRelatedInfo from '@/components/desk/contacts/ContactRelatedInfo.vue'

export default {
	name: 'Contact',
	props: ['contactId'],
	components: {
		ContactInfo,
		ContactRelatedInfo
	},

}
</script>