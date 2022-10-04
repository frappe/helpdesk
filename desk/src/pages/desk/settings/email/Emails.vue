<template>
	<div class="mt-[9px]">
		<ListManager
			class="px-[16px]"
			:options="{
				cache: ['EmailAccounts', 'Settings'],
				doctype: 'Email Account',
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
				filters: [['IMAP Folder', 'append_to', 'in', ['Ticket']]],
				start_page: initialPage,
				route_query_pagination: true,
			}"
		>
			<template #body="{ manager }">
				<EmailList :manager="manager" />
			</template>
		</ListManager>
	</div>
</template>
<script>
import { inject } from "vue"
import EmailList from "@/components/desk/settings/emails/EmailList.vue"
import ListManager from "@/components/global/ListManager.vue"

export default {
	name: "Emails",
	components: {
		EmailList,
		ListManager,
	},
	data() {
		return {
			initialPage: 1,
		}
	},
	setup() {
		const viewportWidth = inject("viewportWidth")

		return {
			viewportWidth,
		}
	},
	mounted() {
		this.$event.emit("set-selected-setting", "Email Accounts")
		this.$event.emit("show-top-panel-actions-settings", "Email Accounts")

		this.initialPage = parseInt(
			this.$route.query.page ? this.$route.query.page : 1
		)
	},
}
</script>
