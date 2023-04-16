<template>
	<div class="flex flex-col px-4">
		<ListManager
			:options="{
				cache: ['EmailAccounts', 'Settings'],
				doctype: 'Email Account',
				urlQueryFilters: true,
				saveFiltersLocally: true,
				fields: [
					'email_account_name',
					'email_id',
					'service',
					'enable_incoming',
					'default_incoming',
					'enable_outgoing',
					'default_outgoing',
				],
				limit: 20,
				filters: [['IMAP Folder', 'append_to', 'in', ['HD Ticket']]],
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:options="{
						name: 'Email',
						base: '12',
						listTitle: 'Email Accounts',
						filterBox: true,
						presetFilters: true,
						fields: {
							email_account_name: {
								label: 'Name',
								width: '3',
							},
							email_id: {
								label: 'Email',
								width: '2',
							},
							service: {
								label: 'Service',
								width: '2',
							},
							default_incoming: {
								label: 'Incoming',
								width: '2',
							},
							default_outgoing: {
								label: 'Outgoing',
								width:'2'
							
							},
						},
					}"
					class="text-base h-[calc(100vh-9.5rem)] pt-4"
					@add-item="
						() => {
							$router.push('/settings/emails/new')
						}
					"
				>
					<template #field-email_account_name="{ row }">
						<div class="w-full group flex items-center">
							<router-link
								:to="{
									path: `/settings/emails/${row.email_account_name}`,
								}"
								class="text-base text-gray-600 font-inter hover:text-gray-900"
							>
								<div>
									{{ `${row.email_account_name}` }}
								</div>
							</router-link>
						</div>
					</template>
					<template #field-email_id="{ row }"
						><div class="text-base text-gray-600 font-inter">
							{{ `${row.email_id}` }}
						</div>
					</template>
					<template #field-service="{ row }"
						><div class="text-base text-gray-600 font-inter">
							{{ `${row.service}` }}
						</div>
					</template>
					<template #field-default_incoming="{ row }">
						<a
							title="Default incoming"
							class="w-full group flex items-center"
						>
							<CustomIcons
								v-if="row.default_incoming"
								name="circle-check"
								class="w-[16px] h-[16px] fill-blue-500"
							/> </a
					></template>
					<template #field-default_outgoing="{ row }">
						<a title="Default outgoing">
							<CustomIcons
								v-if="row.default_outgoing"
								name="circle-check"
								class="w-[16px] h-[16px] fill-blue-500"
							/> </a
					></template>
				</ListViewer>
			</template>
		</ListManager>
	</div>
</template>
<script>
import { inject } from "vue"
import EmailList from "@/components/desk/settings/emails/EmailList.vue"
import ListManager from "@/components/global/ListManager.vue"
import ListViewer from "@/components/global/ListViewer.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "Emails",
	components: {
		EmailList,
		ListManager,
		ListViewer,
		CustomIcons,
	},
	mounted() {
		this.$event.emit("set-selected-setting", "Email Accounts")
	},
	setup() {
		const viewportWidth = inject("viewportWidth")

		return {
			viewportWidth,
		}
	},
}
</script>
